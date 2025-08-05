class Country:
    def __init__(self, string, name, iso2):
        self.name_and_iso2 = string
        self.name = name
        self.iso2 = iso2
    @staticmethod
    def fromString(string):
        try:
            name, iso2 = string.split(" - ")
        except AttributeError:
            name = float('nan')
            iso2 = float('nan')
        return Country(string, name, iso2)
    
    def isinEurope(self):
        import pandas as pd
        european_countries = pd.read_csv("data/transport/European_countries.csv", sep = ";", dtype= {"Country": str, "Code": str})
        test = self.iso2 in list(european_countries["Code"])
        return test