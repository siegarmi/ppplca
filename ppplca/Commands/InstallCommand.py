class InstallCommand:

    def __init__(self):
        pass
    
    def handle(self):
        self.publish_files("config.ini")
        self.publish_files("Processing_data.xlsx")
        self.publish_files("value_chains_test.xlsx")
        self.publish_database_folder()
    
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
    def publish_database_folder():
        print("Publishing database folder...")