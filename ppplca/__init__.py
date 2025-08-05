
def install():
    from Commands.InstallCommand import InstallCommand
    installcommand = InstallCommand()
    installcommand.handle()

def setup():
    from Commands.SetupDatabaseCommand import SetupDatabaseCommand
    setupdatabasecommand = SetupDatabaseCommand()
    setupdatabasecommand.handle()

def run():
    from Commands.RunCommand import RunCommand
    rundatabasecommand = RunCommand()
    rundatabasecommand.handle()