
🗑️ Windows Duplicate File Finder
A powerful desktop application built with Python and Tkinter to find, preview, and safely delete duplicate files on Windows. It features a side-by-side preview pane, multi-folder scanning, and multi-threaded processing so the UI never freezes during a scan.

App Screenshot(Note: Add a screenshot named screenshot.png to your folder to make this image show up)

✨ Features
Multi-Folder Scanning: Add multiple specific folders to scan at the same time.
Smart Filtering: Filter by file extensions (e.g., jpg,png) and minimum file size.
Side-by-Side Preview: Click any duplicate file to instantly preview it. Supports images (JPG, PNG, GIF) and text files (TXT, CSV, PY, JSON, etc.).
Multi-threaded Engine: Scans happen in the background. You can interact with the app without it freezing.
Two-Stage Detection: Groups files by size first, then computes MD5 hashes for 100% accuracy.
Safe Deletion: Delete individual selected files or use "Keep One Per Group" to automatically clean up duplicates.
Space Savings Tracker: Shows exactly how much disk space you are wasting with duplicates.
🛠️ Requirements
Windows OS
Python 3.x
Pillow library (for image previews)
🚀 How to Run
Clone or download this repository.
Open Command Prompt and install the required library:
pip install Pillow
Run the application:
bash

python duplicate_finder.py
📦 How to Create a Standalone .exe
If you want to run this as a native Windows app without Python installed, you can compile it into a single .exe file using PyInstaller:

Install PyInstaller:
bash

pip install pyinstaller
Build the executable:
bash

pyinstaller --onefile --noconsole duplicate_finder.py
Find your new duplicate_finder.exe inside the dist/ folder!
📝 Usage Guide
Click Add Folder... to select the directories you want to scan.
Set your filters (Min size, Extensions, Include subfolders).
Click Scan for Duplicates.
Once the scan is complete, click on any file in the left list to see a preview on the right.
Select the files you want to delete (use Ctrl/Shift for multi-select) and click Delete Selected, or click Keep One Per Group to automatically select duplicates for deletion.