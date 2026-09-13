import os
import hashlib
import threading
import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from collections import defaultdict

# Try to import Pillow for image previews (optional but recommended)
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class DuplicateFileFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("Duplicate File Finder")
        self.root.geometry("1200x700") # Wider window to accommodate side-by-side

        self.selected_folders = []
        self.include_subfolders = tk.BooleanVar(value=True)
        self.min_size = tk.StringVar(value="0")
        self.file_ext = tk.StringVar()
        self.scan_in_progress = False
        self.preview_img = None  # To prevent garbage collection of images

        self.create_widgets()

    # ---------- UI ----------
    def create_widgets(self):
        # --- Top: scan settings ---
        top = ttk.LabelFrame(self.root, text="Scan Settings", padding=10)
        top.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(top, text="Folders to Scan:").grid(row=0, column=0, sticky=tk.NW, pady=2)
        
        list_frame = ttk.Frame(top)
        list_frame.grid(row=0, column=1, columnspan=4, sticky=tk.EW, pady=2)
        
        self.folder_listbox = tk.Listbox(list_frame, height=3, selectmode=tk.SINGLE)
        self.folder_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)

        list_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.folder_listbox.yview)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.folder_listbox.config(yscrollcommand=list_scroll.set)

        btn_frame = ttk.Frame(top)
        btn_frame.grid(row=0, column=5, padx=5, sticky=tk.NS)
        ttk.Button(btn_frame, text="Add Folder...", command=self.add_folder).pack(pady=2, fill=tk.X)
        ttk.Button(btn_frame, text="Remove", command=self.remove_folder).pack(pady=2, fill=tk.X)
        ttk.Button(btn_frame, text="Clear All", command=self.clear_folders).pack(pady=2, fill=tk.X)

        ttk.Label(top, text="Min size (KB):").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(top, textvariable=self.min_size, width=10).grid(row=1, column=1, sticky=tk.W, pady=5)

        ttk.Label(top, text="Extensions (e.g. jpg,png,pdf):").grid(row=1, column=2, sticky=tk.E, padx=10)
        ttk.Entry(top, textvariable=self.file_ext, width=25).grid(row=1, column=3, pady=5)
        ttk.Checkbutton(top, text="Include subfolders", variable=self.include_subfolders).grid(row=1, column=4, sticky=tk.W)

        top.columnconfigure(1, weight=1)

        # --- Action buttons ---
        btn = ttk.Frame(self.root)
        btn.pack(fill=tk.X, padx=10, pady=5)

        self.scan_btn = ttk.Button(btn, text="Scan for Duplicates", command=self.start_scan)
        self.scan_btn.pack(side=tk.LEFT)

        self.delete_btn = ttk.Button(btn, text="Delete Selected", command=self.delete_selected, state=tk.DISABLED)
        self.delete_btn.pack(side=tk.LEFT, padx=5)

        self.keep_one_btn = ttk.Button(btn, text="Keep One Per Group", command=self.keep_one_per_group, state=tk.DISABLED)
        self.keep_one_btn.pack(side=tk.LEFT, padx=5)

        self.open_btn = ttk.Button(btn, text="Open File Location", command=self.open_location, state=tk.DISABLED)
        self.open_btn.pack(side=tk.LEFT, padx=5)

        # --- Progress ---
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=10, pady=2)

        self.status_var = tk.StringVar(value="Ready. Add specific folders and click Scan.")
        ttk.Label(self.root, textvariable=self.status_var).pack(anchor=tk.W, padx=10)

        # --- Results & Preview Split (Horizontal / Side-by-Side) ---
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left Pane: Results tree
        res = ttk.LabelFrame(paned, text="Duplicate Files (select leaf rows to delete)", padding=5)
        paned.add(res, weight=3) # Takes up 75% of width initially

        self.tree = ttk.Treeview(res, columns=('size', 'modified'), show='tree headings', selectmode='extended')
        self.tree.heading('#0', text='File Path / Group')
        self.tree.heading('size', text='Size (KB)')
        self.tree.heading('modified', text='Modified')
        self.tree.column('#0', width=450)
        self.tree.column('size', width=80, anchor=tk.E)
        self.tree.column('modified', width=120)
        self.tree.bind('<<TreeviewSelect>>', self.on_item_selected)

        vsb = ttk.Scrollbar(res, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(res, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        vsb.grid(row=0, column=1, sticky=tk.NS)
        hsb.grid(row=1, column=0, sticky=tk.EW)
        res.rowconfigure(0, weight=1)
        res.columnconfigure(0, weight=1)

        # Right Pane: Preview
        preview_frame = ttk.LabelFrame(paned, text="File Preview", padding=10)
        paned.add(preview_frame, weight=1) # Takes up 25% of width initially

        # Container to help center the preview
        preview_container = ttk.Frame(preview_frame)
        preview_container.pack(expand=True, fill=tk.BOTH)
        preview_container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.preview_label = ttk.Label(preview_container, text="Select a file\nto preview", anchor='center', justify='center')
        self.preview_label.pack()

        self.preview_text = tk.Text(preview_container, wrap=tk.WORD, state=tk.DISABLED, width=40, height=15)
        # Packed dynamically when needed

        # --- Bottom info ---
        self.info_var = tk.StringVar(value="No duplicates found yet.")
        ttk.Label(self.root, textvariable=self.info_var).pack(anchor=tk.W, padx=10, pady=5)

    # ---------- Folder Actions ----------
    def add_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            if folder not in self.selected_folders:
                self.selected_folders.append(folder)
                self.folder_listbox.insert(tk.END, folder)

    def remove_folder(self):
        selected_indices = self.folder_listbox.curselection()
        if not selected_indices: return
        for idx in reversed(selected_indices):
            self.folder_listbox.delete(idx)
            self.selected_folders.pop(idx)

    def clear_folders(self):
        self.folder_listbox.delete(0, tk.END)
        self.selected_folders.clear()

    # ---------- Preview Logic ----------
    def on_item_selected(self, event):
        selected = self.tree.selection()
        if not selected: return
        
        item = selected[0]
        text = self.tree.item(item, 'text')
        
        # Clear previous preview
        self.preview_label.pack_forget()
        self.preview_text.pack_forget()
        
        if text.startswith('[Group'):
            self.preview_label.config(image='', text="Select an individual file\nto preview")
            self.preview_label.pack()
            return

        self.update_preview(text)

    def update_preview(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()
        
        # 1. Try to show Image Preview
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp'] and PIL_AVAILABLE:
            try:
                img = Image.open(filepath)
                img.thumbnail((350, 500)) # Resize to fit nicely in side panel
                self.preview_img = ImageTk.PhotoImage(img)
                self.preview_label.config(image=self.preview_img, text='')
                self.preview_label.pack()
                return
            except Exception:
                pass # Fall through to text if image is corrupt
            
        # 2. Try to show Text Preview
        if ext in ['.txt', '.log', '.csv', '.py', '.js', '.md', '.ini', '.json', '.xml', '.html']:
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(2000) # Read first 2000 chars
                self.preview_text.config(state=tk.NORMAL)
                self.preview_text.delete('1.0', tk.END)
                self.preview_text.insert(tk.END, content)
                self.preview_text.config(state=tk.DISABLED)
                self.preview_text.pack(fill=tk.BOTH, expand=True)
                return
            except Exception:
                pass

        # 3. Fallback for other files
        self.preview_label.config(image='', text=f"Preview not available for:\n{os.path.basename(filepath)}\n(.{ext.strip('.')} file)")
        self.preview_label.pack()

    # ---------- Scanning Actions ----------
    def start_scan(self):
        if self.scan_in_progress: return
        if not self.selected_folders:
            messagebox.showerror("Error", "Please add at least one specific folder to scan.")
            return

        for folder in self.selected_folders:
            if not os.path.isdir(folder):
                messagebox.showerror("Error", f"Folder not found or inaccessible:\n{folder}")
                return

        for item in self.tree.get_children():
            self.tree.delete(item)

        self.scan_in_progress = True
        self.scan_btn.config(state=tk.DISABLED)
        self.delete_btn.config(state=tk.DISABLED)
        self.keep_one_btn.config(state=tk.DISABLED)
        self.open_btn.config(state=tk.DISABLED)
        self.progress.start()
        self.status_var.set("Scanning...")
        self.info_var.set("")

        threading.Thread(target=self.scan_worker, args=(self.selected_folders,), daemon=True).start()

    def scan_worker(self, folders):
        try:
            self._set_status("Collecting file list...")
            files = self.collect_files(folders)

            self._set_status(f"Grouping {len(files)} files by size...")
            size_groups = defaultdict(list)
            for f in files:
                try:
                    size_groups[os.path.getsize(f)].append(f)
                except OSError:
                    continue
            potential = {s: fps for s, fps in size_groups.items() if len(fps) > 1}

            self._set_status("Computing hashes for potential duplicates...")
            hash_groups = defaultdict(list)
            for size, fpaths in potential.items():
                for fp in fpaths:
                    h = self.compute_hash(fp)
                    if h:
                        hash_groups[(size, h)].append(fp)

            duplicates = {k: v for k, v in hash_groups.items() if len(v) > 1}
            self.root.after(0, lambda: self.display_results(duplicates))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.root.after(0, self.scan_complete)

    def collect_files(self, folders):
        files = []
        seen_paths = set()
        include_sub = self.include_subfolders.get()
        try:
            min_size_bytes = int(float(self.min_size.get() or 0) * 1024)
        except ValueError:
            min_size_bytes = 0

        ext_filter = None
        ext_text = self.file_ext.get().strip()
        if ext_text:
            ext_filter = {'.' + e.strip().lower().lstrip('.') for e in ext_text.split(',')}

        for folder in folders:
            if include_sub:
                walker = os.walk(folder)
                for dirpath, _, filenames in walker:
                    for fn in filenames:
                        fp = os.path.join(dirpath, fn)
                        if fp in seen_paths: continue
                        if not os.path.isfile(fp): continue
                        if ext_filter and os.path.splitext(fn)[1].lower() not in ext_filter: continue
                        try:
                            if os.path.getsize(fp) >= min_size_bytes:
                                files.append(fp)
                                seen_paths.add(fp)
                        except OSError: pass
            else:
                for fn in os.listdir(folder):
                    fp = os.path.join(folder, fn)
                    if fp in seen_paths: continue
                    if not os.path.isfile(fp): continue
                    if ext_filter and os.path.splitext(fn)[1].lower() not in ext_filter: continue
                    try:
                        if os.path.getsize(fp) >= min_size_bytes:
                            files.append(fp)
                            seen_paths.add(fp)
                    except OSError: pass
        return files

    @staticmethod
    def compute_hash(filepath, chunk_size=65536):
        try:
            h = hashlib.md5()
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk: break
                    h.update(chunk)
            return h.hexdigest()
        except (OSError, PermissionError):
            return None

    def display_results(self, duplicates):
        group_count = 0
        total_files = 0
        total_wasted = 0

        for (size, _h), files in duplicates.items():
            group_count += 1
            label = f"[Group {group_count}] {len(files)} duplicates — {self.format_size(size)} each"
            gid = self.tree.insert('', tk.END, text=label, open=True)
            for fp in files:
                try:
                    mtime = os.path.getmtime(fp)
                    mod = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
                    self.tree.insert(gid, tk.END, text=fp, values=(f"{size/1024:.1f}", mod))
                    total_files += 1
                except OSError: pass
            total_wasted += size * (len(files) - 1)

        self.info_var.set(f"Found {group_count} duplicate groups, {total_files} files. Potential space savings: {self.format_size(total_wasted)}")

        if duplicates:
            self.delete_btn.config(state=tk.NORMAL)
            self.keep_one_btn.config(state=tk.NORMAL)
            self.open_btn.config(state=tk.NORMAL)
            self.status_var.set("Scan complete. Select files to delete.")
        else:
            self.status_var.set("No duplicates found.")

    def scan_complete(self):
        self.scan_in_progress = False
        self.progress.stop()
        self.scan_btn.config(state=tk.NORMAL)

    # ---------- Deletion ----------
    def delete_selected(self):
        selected = self.tree.selection()
        files_to_delete = []
        items_to_delete = []
        for item in selected:
            text = self.tree.item(item, 'text')
            if text.startswith('[Group'): continue
            files_to_delete.append(text)
            items_to_delete.append(item)

        if not files_to_delete:
            messagebox.showinfo("Info", "Please select individual file rows (not group headers).")
            return

        if not messagebox.askyesno("Confirm Delete", f"Permanently delete {len(files_to_delete)} file(s)?\nThis cannot be undone."): return

        deleted = 0
        errors = []
        for fp, item in zip(files_to_delete, items_to_delete):
            try:
                os.remove(fp)
                deleted += 1
                parent = self.tree.parent(item)
                self.tree.delete(item)
                if parent and not self.tree.get_children(parent):
                    self.tree.delete(parent)
            except OSError as e:
                errors.append(f"{fp}: {e}")

        msg = f"Deleted {deleted} file(s)."
        if errors:
            msg += "\n\nErrors:\n" + "\n".join(errors[:10])
            if len(errors) > 10: msg += f"\n... and {len(errors) - 10} more"
        messagebox.showinfo("Result", msg)
        
        # Clear preview after deletion
        self.preview_label.pack_forget()
        self.preview_text.pack_forget()
        self.preview_label.config(image='', text="Select a file\nto preview")
        self.preview_label.pack()

    def keep_one_per_group(self):
        to_select = []
        for group in self.tree.get_children():
            children = self.tree.get_children(group)
            if len(children) > 1:
                to_select.extend(children[1:])
        if not to_select:
            messagebox.showinfo("Info", "No duplicates to delete.")
            return

        self.tree.selection_set(to_select)
        if not messagebox.askyesno("Confirm Delete", f"Delete {len(to_select)} duplicate file(s), keeping one per group?"): return

        deleted = 0
        for item in to_select:
            fp = self.tree.item(item, 'text')
            try:
                os.remove(fp)
                deleted += 1
            except OSError: pass

        messagebox.showinfo("Result", f"Deleted {deleted} duplicate file(s). Please re-scan to refresh the list.")
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.info_var.set(f"Deleted {deleted} duplicate files. Re-scan to view remaining duplicates.")

    def open_location(self):
        selected = self.tree.selection()
        if not selected: return
        text = self.tree.item(selected[0], 'text')
        if text.startswith('[Group'): return
        folder = os.path.dirname(text)
        try:
            os.startfile(folder)
        except OSError as e:
            messagebox.showerror("Error", str(e))

    # ---------- Helpers ----------
    def _set_status(self, msg):
        self.root.after(0, lambda: self.status_var.set(msg))

    @staticmethod
    def format_size(num_bytes):
        size = float(num_bytes)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


if __name__ == "__main__":
    root = tk.Tk()
    app = DuplicateFileFinder(root)
    root.mainloop()