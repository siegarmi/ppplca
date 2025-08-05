class Activity:
    def __init__(self, name, activity):
        self.name = name
        self.object = activity

    def __str__(self) -> str:
        return self.name