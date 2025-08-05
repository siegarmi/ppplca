class InstallCommand:

    def __init__(self):
        pass
    
    def handle(self):
        self.publish_files("config.ini")
        self.publish_files("Processing_data.xlsx")
        self.publish_files("value_chains_test.xlsx")
        self.store_afdb_in_database_folder()
    
    @staticmethod
    def publish_files(filename):
        import shutil
        import os
        import importlib.resources as resources

        print(f"Publishing {filename} files...")

        package = "ppplca.stubs"  # adjust if your folder is nested differently
        with resources.path(package, filename) as src_path:
            dest_path = os.path.join(os.getcwd(), filename)
            shutil.copyfile(src_path, dest_path)
            print(f"Copied {filename} to {dest_path}")

    @staticmethod
    def store_afdb_in_database_folder():
        import os
        import shutil
        from tkinter import Tk, filedialog

        print("Publishing database folder...")

        # Hide the main Tkinter window
        root = Tk()
        root.withdraw()

        # Open a file dialog to select a CSV file
        file_path = filedialog.askopenfilename(
            title="Select a CSV file",
            filetypes=[("CSV files", "*.csv")]
        )

        if not file_path:
            print("No file selected.")
            return

        # Create 'Database' folder in current working directory
        database_dir = os.path.join(os.getcwd(), "Database")
        os.makedirs(database_dir, exist_ok=True)

        # Copy the selected CSV to the Database folder
        file_name = os.path.basename(file_path)
        dest_path = os.path.join(database_dir, file_name)
        shutil.copyfile(file_path, dest_path)

        print(f"✅ {file_name} has been copied to the 'Database' folder.")