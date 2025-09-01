class SetupDatabaseCommand:

    def __init__(self):
        pass

    def handle(self):
        import bw2data as bd
        import time
        from ppplca.config import config

        bd.projects.dir
        bd.projects.set_current(config('project.name'))
        answer = input("Database setup is starting, it will take around 48 hours to complete on a regular laptop. Are you sure you want to continue? [Y/n]")
        if answer.lower() != "y":
            current_time = time.localtime()
            print(f"[{time.strftime('%H:%M:%S', current_time)}] Database setup aborted. Rerun the command...")
            return 
        print(f"Database setup is starting...")
        
        start = time.time()
        ei_name, bio_name = self.load_ecoinvent_database()
        af_name = self.load_agrifootprint_database(ei_name, bio_name)
        eidb = bd.Database(ei_name)
        afdb = bd.Database(af_name)
        eidb_reg, afdb_reg = self.regionalize_databases(ei_name, af_name)
        self.create_electricity_market_groups(eidb_reg)
        self.create_agri_activities(eidb_reg, afdb_reg)
        self.create_heat_activities(eidb_reg)
        self.create_electricity_market_groups(eidb)
        self.create_agri_activities(eidb, afdb)
        self.create_heat_activities(eidb)

        end = time.time()
        print(f"Database setup completed in {end - start} seconds.")

    @staticmethod
    def load_ecoinvent_database():
        import bw2data as bd
        import bw2io as bi
        from ecoinvent_interface import Settings
        from ppplca.config import config

        print("Loading ecoinvent database...")
        ei_name = "ecoinvent-3.10-cutoff"
        bio_name = "ecoinvent-3.10-biosphere"
        my_settings = Settings(username=config('database.username'), password=config('database.password'))
        if ei_name in bd.databases and bio_name in bd.databases:
            print(ei_name + " and " + bio_name + " have already been imported.")
        elif ei_name in bd.databases and not bio_name in bd.databases:
            print(ei_name + " has already been imported." + bio_name + " is missing. Please, delete " + ei_name + " and run the command again.")
        else:
            bi.import_ecoinvent_release("3.10","cutoff",my_settings.username,my_settings.password)

        print("Ecoinvent database loaded successfully.")

        return ei_name, bio_name

    @staticmethod
    def load_agrifootprint_database(ei_name, bio_name):
        from ppplca.Actions.import_agrifootprint_db_functions import import_agrifootprint

        import_agrifootprint(ei_name,bio_name)

        af_name = "agrifootprint 6.3 all allocations"

        return af_name
    
    @staticmethod
    def regionalize_databases(ei_name, af_name):
        import bw2data as bd
        from ppplca.Actions.bw_base_set_up import bw_set_up, regionalize_db

        bw_set_up()
        regionalize_db(ei_name)
        regionalize_db(af_name)

        eidb_reg = bd.Database("ecoinvent-3.10-cutoff_regionalized")
        afdb_reg = bd.Database("agrifootprint 6.3 all allocations_regionalized")

        return eidb_reg, afdb_reg
    
    @staticmethod
    def create_electricity_market_groups(eidb_reg):
        import pandas as pd
        import importlib.resources as resources
        import numpy as np

        with resources.open_text("ppplca.data.grid_shares","Electricity_grid_shares_CN_pea.csv") as f:
            electricity_share_CN_pea = pd.read_csv(f, sep = ";", decimal = ".", dtype= {"Region": str, "Grid": str, "Area": np.float64, "Share": np.float64})
        with resources.open_text("ppplca.data.grid_shares","Electricity_grid_shares_CN_soy.csv") as f:
            electricity_share_CN_soy = pd.read_csv(f, sep = ";", decimal = ".", dtype= {"Region": str, "Grid": str, "Area": np.float64, "Share": np.float64})
        with resources.open_text("ppplca.data.grid_shares","Electricity_grid_shares_CN_wheat.csv") as f:
            electricity_share_CN_wheat = pd.read_csv(f, sep = ";", decimal = ".", dtype= {"Region": str, "Grid": str, "Area": np.float64, "Share": np.float64})
        with resources.open_text("ppplca.data.grid_shares","Electricity_grid_shares_US_soy.csv") as f:
            electricity_share_US_soy = pd.read_csv(f, sep = ";", decimal = ".", dtype= {"Region": str, "Grid": str, "Area": np.float64, "Share": np.float64})
        with resources.open_text("ppplca.data.grid_shares","Electricity_grid_shares_US_wheat.csv") as f:
            electricity_share_US_wheat = pd.read_csv(f, sep = ";", decimal = ".", dtype= {"Region": str, "Grid": str, "Area": np.float64, "Share": np.float64}) 

        SetupDatabaseCommand.create_electricity_market_group_processes("CN-SGCC",electricity_share_CN_pea,"Pea",eidb_reg)
        SetupDatabaseCommand.create_electricity_market_group_processes("CN-SGCC",electricity_share_CN_soy,"Soy",eidb_reg)
        SetupDatabaseCommand.create_electricity_market_group_processes("CN-SGCC",electricity_share_CN_wheat,"Wheat",eidb_reg)
        SetupDatabaseCommand.create_electricity_market_group_processes("US",electricity_share_US_soy,"Soy",eidb_reg)
        SetupDatabaseCommand.create_electricity_market_group_processes("US",electricity_share_US_wheat,"Wheat",eidb_reg)

    @staticmethod
    def create_electricity_market_group_processes(country,grid_shares,product,db):

        if [act for act in db if "market group for electricity used in " + product + " processing, low voltage" == act["name"] and country[:2] in act["location"]] != []:
            print("Electricity market group for " + product + " processing in " + country[:2] + " already exists.")
        else:
            existing_electricity_market_group = [act for act in db if "market group for electricity, low voltage" == act['name'] and country == act['location']][0]

            new_electricity_market_group = existing_electricity_market_group.copy()
            new_electricity_market_group["name"] = "market group for electricity used in " + product + " processing, low voltage"
            if country == "CN-SGCC":
                new_electricity_market_group["location"] = "CN"
                new_electricity_market_group.save()
            for exchange in [exc for exc in new_electricity_market_group.exchanges() if exc["type"] == "technosphere"]:
                exchange_input = [act for act in db if exchange["input"][1] == act['code']][0]
                if exchange_input["location"] in grid_shares["Grid"].to_list():
                    exchange["amount"] = grid_shares.loc[grid_shares["Grid"]==exchange_input["location"]]["Share"].to_list()[0]
                    exchange.save()
                else:
                    exchange.delete()
            if country == "CN-SGCC":
                central_grid = [act for act in db if "market for electricity, low voltage" == act['name'] and "CN-CSG" == act['location']][0]
                new_electricity_market_group.new_exchange(input=central_grid.key,amount=grid_shares.loc[grid_shares["Grid"]=="CN-CSG"]["Share"].to_list()[0],unit="kilowatt hour",type="technosphere").save()
                new_electricity_market_group.new_exchange(input=new_electricity_market_group.key,amount=1,unit="kilowatt hour",type="production").save()
            new_electricity_market_group.save()
            print(new_electricity_market_group["name"] + " created.")

    @staticmethod
    def create_agri_activities(eidb_reg, afdb_reg):
        import pandas as pd
        from ppplca.Actions.CreateAgriActivities import CreateAgriActivities

        countries = pd.read_excel('value_chains_test.xlsx', sheet_name="Countries (don't change)")

        crop_names = ["Peas","Soybeans","Wheat"]
        for country in countries["Code"]:
            if SetupDatabaseCommand.isinEurope(country):
                for crop_name in crop_names:
                    CreateAgriActivities.create_missing_agri_activities(country,crop_name,eidb_reg,afdb_reg)
    
    @staticmethod
    def isinEurope(country):
        import pandas as pd
        import importlib.resources as resources

        with resources.open_text("ppplca.data.transport","European_countries.csv") as f:
            european_countries = pd.read_csv(f, sep = ";", dtype= {"Country": str, "Code": str})
        test = country in list(european_countries["Code"])
        return test
    
    @staticmethod
    def create_heat_activities(eidb_reg):
        import pandas as pd
        from ppplca.Actions.CreateHeatActivities import CreateHeatActivities

        countries = pd.read_excel('value_chains_test.xlsx', sheet_name="Countries (don't change)")

        for country in countries["Code"]:
            if country == "CN":
                for crop_name in ["Peas","Soybeans","Wheat"]:
                    test_activity = [act for act in eidb_reg if "custom_heat_process_" + str(country) + "_" + str(crop_name) in act['code'] and country in act['location']]
                    if test_activity == []:
                        print("Creating heat production activity for " + crop_name + " in " + country + ".")
                        CreateHeatActivities.create_heat_production_process(country,crop_name,eidb_reg)
                    else:
                        print("Heat production activity for " + crop_name + " in " + country + " is already present.")
            elif country == "US":
                for crop_name in ["Soybeans","Wheat"]:
                    test_activity = [act for act in eidb_reg if "custom_heat_process_" + str(country) + "_" + str(crop_name) in act['code'] and country in act['location']]
                    if test_activity == []:
                        print("Creating heat production activity for " + crop_name + " in " + country + ".")
                        CreateHeatActivities.create_heat_production_process(country,crop_name,eidb_reg)
                    else:
                        print("Heat production activity for " + crop_name + " in " + country + " is already present.")
            else:
                test_activity = [act for act in eidb_reg if "custom_heat_process_" + str(country) + "_" in act['code'] and country in act['location']]
                if test_activity == []:
                        print("Creating heat production activity for in " + country + ".")
                        CreateHeatActivities.create_heat_production_process(country,"",eidb_reg)
                else:
                    print("Heat production activity for in " + country + " is already present.")