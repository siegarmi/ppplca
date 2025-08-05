class Exchange:
    def __init__(self, name, formula, unit):
        self.name = name
        self.formula = formula	
        self.unit = unit

    def __str__(self) -> str:
        return self.name