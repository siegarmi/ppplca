
def install():
    from ppplca.Commands.InstallCommand import InstallCommand
    installcommand = InstallCommand()
    installcommand.handle()

def setup():
    answer = input("Have you updated the config.ini file and saved the agrifootprint database? [Y/n]: ")
    if answer.lower() != "y":
        print("Please update the file and save the database before running the setup.")
        return
    from ppplca.Commands.SetupDatabaseCommand import SetupDatabaseCommand
    setupdatabasecommand = SetupDatabaseCommand()
    setupdatabasecommand.handle()

def run(file="value_chains.xlsx", sheet_name = None):
    answer = input(f"Have you updated the Processing_data.xlsx and {file} files? [Y/n]: ")
    if answer.lower() != "y":
        print("Please update the filese before running the setup.")
        return
    from ppplca.Commands.RunCommand import RunCommand
    rundatabasecommand = RunCommand()
    rundatabasecommand.handle(file, sheet_name)