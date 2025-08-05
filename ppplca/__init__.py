
def install():
    from ppplca.Commands.InstallCommand import InstallCommand
    installcommand = InstallCommand()
    installcommand.handle()

def setup():
    from ppplca.Commands.SetupDatabaseCommand import SetupDatabaseCommand
    setupdatabasecommand = SetupDatabaseCommand()
    setupdatabasecommand.handle()

def run():
    from ppplca.Commands.RunCommand import RunCommand
    rundatabasecommand = RunCommand()
    rundatabasecommand.handle()