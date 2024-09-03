import os
import shutil
from datetime import datetime
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image
import PIL.ExifTags
import subprocess
from threading import Thread

class PhotoOrganizerGUI:
    def __init__(self, master):
        self.master = master
        master.title("Photo and Video Organizer")
        master.geometry("567x318")

        self.create_widgets()

    def create_widgets(self):
        # Source folder selection
        ttk.Label(self.master, text="Source folder:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.source_entry = ttk.Entry(self.master, width=50)
        self.source_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(self.master, text="Browse", command=self.select_source).grid(row=0, column=2, padx=5, pady=5)

        # Destination folder selection
        ttk.Label(self.master, text="Destination folder:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.dest_entry = ttk.Entry(self.master, width=50)
        self.dest_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(self.master, text="Browse", command=self.select_destination).grid(row=1, column=2, padx=5, pady=5)

        # File type selection
        ttk.Label(self.master, text="Select file types to organize:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.photo_var = tk.BooleanVar(value=True)
        self.video_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.master, text="Photos", variable=self.photo_var).grid(row=2, column=1, sticky="w", padx=5, pady=5)
        ttk.Checkbutton(self.master, text="Videos", variable=self.video_var).grid(row=3, column=1, sticky="w", padx=5, pady=5)

        # Organize button
        self.organize_button = ttk.Button(self.master, text="Organize Files", command=self.start_organize)
        self.organize_button.grid(row=4, column=1, pady=20)

        # Progress bar
        self.progress = ttk.Progressbar(self.master, orient="horizontal", length=400, mode="determinate")
        self.progress.grid(row=5, column=0, columnspan=3, padx=5, pady=5)

        # Status label
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(self.master, textvariable=self.status_var)
        self.status_label.grid(row=6, column=0, columnspan=3, padx=5, pady=5)

        # Detailed status bar
        self.detailed_status_var = tk.StringVar()
        self.detailed_status_bar = ttk.Label(self.master, textvariable=self.detailed_status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.detailed_status_bar.grid(row=7, column=0, columnspan=3, sticky="we", padx=5, pady=5)

    def select_source(self):
        folder_selected = filedialog.askdirectory()
        self.source_entry.delete(0, tk.END)
        self.source_entry.insert(0, folder_selected)

    def select_destination(self):
        folder_selected = filedialog.askdirectory()
        self.dest_entry.delete(0, tk.END)
        self.dest_entry.insert(0, folder_selected)

    def get_date_taken(self, file_path):
        try:
            image = Image.open(file_path)
            exif = {
                PIL.ExifTags.TAGS[k]: v
                for k, v in image._getexif().items()
                if k in PIL.ExifTags.TAGS
            }
            date_str = exif.get('DateTimeOriginal', None)
            if date_str:
                return datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
        except:
            pass

        # If exif data is not available, use file creation time
        return datetime.fromtimestamp(os.path.getctime(file_path))

    def get_video_creation_time(self, file_path):
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            metadata = json.loads(result.stdout)
            creation_time = metadata['format']['tags']['creation_time']
            return datetime.strptime(creation_time, '%Y-%m-%dT%H:%M:%S.%fZ')
        except:
            # If ffprobe fails or creation_time is not available, use file creation time
            return datetime.fromtimestamp(os.path.getctime(file_path))

    def start_organize(self):
        source_folder = self.source_entry.get()
        dest_folder = self.dest_entry.get()

        if not source_folder or not dest_folder:
            messagebox.showerror("Error", "Please select both source and destination folders.")
            return

        if not self.photo_var.get() and not self.video_var.get():
            messagebox.showerror("Error", "Please select at least one file type to organize.")
            return

        self.organize_button.config(state="disabled")
        self.progress["value"] = 0
        self.status_var.set("Organizing files...")

        thread = Thread(target=self.organize_files, args=(source_folder, dest_folder))
        thread.start()

    def organize_files(self, source_folder, dest_folder):
        file_list = [f for f in os.listdir(source_folder) if os.path.isfile(os.path.join(source_folder, f))]
        total_files = len(file_list)
        processed_files = 0
        moved_files = 0

        for filename in file_list:
            file_path = os.path.join(source_folder, filename)
            
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')) and self.photo_var.get():
                date_taken = self.get_date_taken(file_path)
                file_type = "photo"
            elif filename.lower().endswith(('.mp4', '.mov', '.avi', '.wmv')) and self.video_var.get():
                date_taken = self.get_video_creation_time(file_path)
                file_type = "video"
            else:
                processed_files += 1
                self.update_status(processed_files, moved_files, total_files)
                continue

            year_month_folder = os.path.join(dest_folder, date_taken.strftime('%Y'), date_taken.strftime('%m'))
            os.makedirs(year_month_folder, exist_ok=True)
            
            new_file_path = os.path.join(year_month_folder, filename)
            shutil.move(file_path, new_file_path)

            processed_files += 1
            moved_files += 1

            self.update_status(processed_files, moved_files, total_files)

        self.status_var.set("Files have been organized successfully!")
        self.organize_button.config(state="normal")
        messagebox.showinfo("Success", "Files have been organized successfully!")

    def update_status(self, processed_files, moved_files, total_files):
        progress_value = int(processed_files / total_files * 100)
        self.progress["value"] = progress_value
        self.status_var.set(f"Processed {processed_files} of {total_files} files")
        
        files_left = total_files - processed_files
        self.detailed_status_var.set(f"Files moved: {moved_files} | Files left: {files_left} | Total files: {total_files}")
        
        self.master.update_idletasks()

if __name__ == "__main__":
    root = tk.Tk()
    my_gui = PhotoOrganizerGUI(root)
    root.mainloop()
