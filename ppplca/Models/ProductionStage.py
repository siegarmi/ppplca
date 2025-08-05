class ProductionStage:
    def __init__(self, name, country, is_transported, country_last_production_stage):
        from ppplca.Models.Country import Country
        self.name = name
        self.country = Country.fromString(country)
        self.is_transported = is_transported
        self.country_last_production_stage = Country.fromString(country_last_production_stage)
        self.exchanges = []
        self.activities = {}

    def loadAgriExchange(self):
        from ppplca.Models.Exchange import Exchange
        exchange = Exchange("crop","1","kg")
        self.exchanges.append(exchange)

    def loadExchanges(self, exchanges_input):
        from ppplca.Models.Exchange import Exchange
        for i in range(0,len(exchanges_input)):
            exchange = Exchange(exchanges_input["exchange"].iloc[i],str(exchanges_input["formula"].iloc[i]),exchanges_input["unit"].iloc[i])
            self.exchanges.append(exchange)
    
    def loadTransportExchanges(self):
        from ppplca.Models.Exchange import Exchange

        exchange = Exchange(f'{self.name}_transport','1',"tkm")
        self.exchanges.append(exchange)

    def loadActivities(self, crop_name, ei_reg_name, af_reg_name, bio_name, user_db_name):
        import lca_algebraic as agb
        import bw2data as bd
        from ppplca.Models.Activity import Activity
        from ppplca.Actions.FindActivityLocation import FindActivityLocation
        from pandas import read_csv

        activity_names = read_csv("Data input/input_files/activity_names/activity_names.csv", sep=";")

        for exchange in self.exchanges:
            activity_key = exchange.name
            if "allocation" in activity_key or "protein_content" in activity_key:
                continue
            elif "input" in activity_key:
                activity_key = activity_key.split("_")[1]
            
            if activity_key == "crop":
                database = af_reg_name
                if crop_name == "Peas":
                    activity_name = f'Peas, dry, dried, at storage {{{self.country.iso2}}} Economic, U'
                elif crop_name == "Soybeans":
                    activity_name = f'Soybeans, dried, at storage {{{self.country.iso2}}} Economic, U'
                elif crop_name == "Wheat":
                    activity_name = f'Wheat grain, dried, at storage {{{self.country.iso2}}} Economic, U'
            elif activity_key == "electricity_mix" and (self.country.iso2 == "US" or self.country.iso2 == "CN"):
                database = ei_reg_name
                if crop_name == "Peas":
                    activity_name = "market group for electricity used in Pea processing, low voltage"
                elif crop_name == "Soybeans":
                    activity_name = "market group for electricity used in Soy processing, low voltage"
                elif crop_name == "Wheat":
                    activity_name = "market group for electricity used in Wheat processing, low voltage"
            elif activity_key == "cultivation" or activity_key == "dehulling" or activity_key == "milling" or activity_key == "defatting" or activity_key == "extraction" or "transport" in activity_key:
                database = user_db_name
                activity_name = activity_key
            else:
                database = ei_reg_name
                activity_name = activity_names[activity_names["key"] == activity_key]["name"].iloc[0]

            if activity_name == "Hexane":
                activity = agb.findActivity('Hexane',categories=["air",],db_name=bio_name,case_sensitive = True)
            else:
                activity_list_temp = [act for act in bd.Database(database) if act["name"] == activity_name and act["location"] == self.country.iso2]
                activity_list_temp = FindActivityLocation.find(activity_list_temp,activity_name,self.country.iso2,crop_name,bd.Database(database))
                activity = activity_list_temp[0]

            self.activities[activity_key] = Activity(activity_key, activity)

    def createTransportActivities(self, ei_reg_name, user_db, params, formula_transported_quantity):
        import lca_algebraic as agb

        exchanges_dict = {}

        if self.country.isinEurope() and self.country_last_production_stage.isinEurope():
            exchange_formula = f'({formula_transported_quantity}) * params["{self.name}_transport_europe"] / 1000' #divided by 1000 to convert kg of transported good into tons because unit is tkm
            transport_europe_act = agb.findActivity('transport, freight, lorry, all sizes, EURO6 to generic market for transport, freight, lorry, unspecified',loc="RER",db_name=ei_reg_name)
            exchanges_dict[transport_europe_act] = eval(exchange_formula)
        else:
            exchange_formula_overseas = f'({formula_transported_quantity}) * params["{self.name}_transport_overseas"] / 1000' #divided by 1000 to convert kg of transported good into tons because unit is tkm
            exchange_formula_shipping = f'({formula_transported_quantity}) * params["{self.name}_transport_shipping"] / 1000' #divided by 1000 to convert kg of transported good into tons because unit is tkm
            exchange_formula_europe_port = f'({formula_transported_quantity}) * params["{self.name}_transport_europe_port"] / 1000' #divided by 1000 to convert kg of transported good into tons because unit is tkm
            transport_overseas_act = agb.findActivity('transport, freight, lorry, all sizes, EURO6 to generic market for transport, freight, lorry, unspecified',loc="RoW",db_name=ei_reg_name)
            transport_shipping_act = agb.findActivity('market for transport, freight, sea, container ship',loc="GLO",db_name=ei_reg_name)
            transport_europe_port_act = agb.findActivity('transport, freight, lorry, all sizes, EURO6 to generic market for transport, freight, lorry, unspecified',loc="RER",db_name=ei_reg_name)
            exchanges_dict[transport_overseas_act] = eval(exchange_formula_overseas)
            exchanges_dict[transport_shipping_act] = eval(exchange_formula_shipping)
            exchanges_dict[transport_europe_port_act] = eval(exchange_formula_europe_port)

        agb.newActivity(user_db,
                f'{self.name}_transport',
                "tkm",
                exchanges= exchanges_dict)

    
    def createForegroundActivities(self, user_db, params):
        import lca_algebraic as agb

        exchanges_dict = {}

        for exchange in self.exchanges:
            activity_key = exchange.name
            if "allocation" in activity_key or "protein_content" in activity_key:
                continue
            elif "input" in activity_key:
                activity_key = activity_key.split("_")[1]
            exchanges_dict[self.activities[activity_key].object] = eval(exchange.formula)

        agb.newActivity(user_db,
                self.name,
                "kg",
                exchanges= exchanges_dict)