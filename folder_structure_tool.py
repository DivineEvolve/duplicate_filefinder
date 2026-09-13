import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

class FolderStructureTool:
    def __init__(self, root):
        self.root = root
        self.root.title("Folder Structure Tool")
        self.root.geometry("600x350")

        self.source_folder = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        # --- Source Selection ---
        top = ttk.LabelFrame(self.root, text="1. Select Source Folder", padding=15)
        top.pack(fill=tk.X, padx=10, pady=10)

        ttk.Entry(top, textvariable=self.source_folder, width=60).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(top, text="Browse...", command=self.browse_source).pack(side=tk.LEFT)

        # --- Actions ---
        actions = ttk.LabelFrame(self.root, text="2. Choose Action", padding=15)
        actions.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Action 1: Export to Text
        ttk.Button(actions, text="Export Structure to Text File", command=self.export_to_text).pack(fill=tk.X, pady=5)
        ttk.Label(actions, text="Creates a .txt file containing a visual tree of all files and folders.").pack(pady=2)

        # Action 2: Clone Empty Folders
        ttk.Button(actions, text="Clone Empty Folder Structure", command=self.clone_structure).pack(fill=tk.X, pady=10)
        ttk.Label(actions, text="Asks for a destination, then creates the exact folder layout there (without files).").pack(pady=2)

        # --- Status ---
        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(self.root, textvariable=self.status_var, font=('Segoe UI', 9, 'italic')).pack(side=tk.BOTTOM, pady=10)

    def browse_source(self):
        folder = filedialog.askdirectory()
        if folder:
            self.source_folder.set(folder)

    def export_to_text(self):
        source = self.source_folder.get()
        if not source or not os.path.isdir(source):
            messagebox.showerror("Error", "Please select a valid source folder.")
            return

        # Ask where to save the text file
        save_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile="folder_structure.txt"
        )
        if not save_path:
            return

        try:
            self.status_var.set("Generating text tree... (This may take a moment for large folders)")
            self.root.update_idletasks()

            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(f"Folder Structure for: {source}\n")
                f.write("="*50 + "\n\n")

                for dirpath, dirnames, filenames in os.walk(source):
                    # Calculate depth for indentation
                    relative_path = os.path.relpath(dirpath, source)
                    if relative_path == '.':
                        depth = 0
                        f.write(f"[{os.path.basename(source)}]\n")
                    else:
                        depth = relative_path.count(os.sep) + 1
                        indent = "    " * depth
                        f.write(f"{indent}[{os.path.basename(dirpath)}]\n")

                    # Write files under the folder
                    file_indent = "    " * (depth + 1)
                    for filename in filenames:
                        f.write(f"{file_indent}{filename}\n")

            self.status_var.set(f"Success! Structure saved to {save_path}")
            messagebox.showinfo("Success", f"Folder structure exported successfully to:\n{save_path}")

        except Exception as e:
            self.status_var.set("Error during export.")
            messagebox.showerror("Error", str(e))

    def clone_structure(self):
        source = self.source_folder.get()
        if not source or not os.path.isdir(source):
            messagebox.showerror("Error", "Please select a valid source folder.")
            return

        # Ask for destination folder
        dest = filedialog.askdirectory(title="Select Destination Folder (where to clone the structure)")
        if not dest:
            return

        try:
            self.status_var.set("Cloning folder structure... (Creating empty directories)")
            self.root.update_idletasks()

            folders_created = 0
            for dirpath, dirnames, filenames in os.walk(source):
                relative_path = os.path.relpath(dirpath, source)
                
                # If it's the root folder itself, map it to destination
                if relative_path == '.':
                    target_path = dest
                else:
                    target_path = os.path.join(dest, relative_path)

                if not os.path.exists(target_path):
                    os.makedirs(target_path, exist_ok=True)
                    folders_created += 1

            self.status_var.set(f"Success! Created {folders_created} folders in {dest}")
            messagebox.showinfo("Success", f"Empty folder structure cloned successfully!\nCreated {folders_created} folders.")

        except Exception as e:
            self.status_var.set("Error during cloning.")
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = FolderStructureTool(root)
    root.mainloop()