class FindActivityLocation:

    @staticmethod
    def isinEurope(country):
        from pandas import read_csv
        import importlib.resources as resources

        with resources.open_text("ppplca.data.transport","European_countries.csv") as f:
            european_countries = read_csv(f, sep = ";")
        test = country in list(european_countries["Code"])
        return test

    @classmethod
    def find(cls,created_exchange,activity_name,country,crop_name,db):

        if created_exchange == [] and "market for electricity, low voltage" == activity_name:
            if country == "CN" and crop_name == "Peas":
                activity_name = "market group for electricity used in Pea processing, low voltage"
            elif country == "CN" and crop_name == "Soybeans":
                activity_name = "market group for electricity used in Soy processing, low voltage"
            elif country == "CN" and crop_name == "Wheat":
                activity_name = "market group for electricity used in Wheat processing, low voltage"
            elif country == "US" and crop_name == "Soybeans":
                activity_name = "market group for electricity used in Soy processing, low voltage"
            elif country == "US" and crop_name == "Wheat":
                activity_name = "market group for electricity used in Wheat processing, low voltage"
            else:
                activity_name = "market group for electricity, low voltage"
            created_exchange = [act for act in db if activity_name == act['name'] and country == act['location']]
        if created_exchange == [] and cls.isinEurope(country) and activity_name == "market for natural gas, high pressure":
            country = "RoE"
            created_exchange = [act for act in db if activity_name == act['name'] and country == act['location']]
        elif created_exchange == [] and cls.isinEurope(country) and (activity_name == "market for tap water" or activity_name == "market for wastewater, average"):
            country = "Europe without Switzerland"
            created_exchange = [act for act in db if activity_name == act['name'] and country == act['location']]
        elif created_exchange == [] and cls.isinEurope(country):
            country = "RER"
            created_exchange = [act for act in db if activity_name == act['name'] and country == act['location']]
        if created_exchange == []:
            country = "RoW"
            created_exchange = [act for act in db if activity_name == act['name'] and country == act['location']]
        if created_exchange == []:
            country = "GLO"
            created_exchange = [act for act in db if activity_name == act['name'] and country == act['location']]

        return created_exchange