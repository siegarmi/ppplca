class RunCommand:

    def __init__(self):
        pass

    def handle(self,file,sheet_name):
        import lca_algebraic as agb
        import bw2data as bd

        self.set_project_name()
        answer = input("Would you like to conduct a regionalized assessment for water use, land use related biodiversity loss, and human health impacts from particulate matter or a non-regionalized assessment using ReCiPe 2016? [regionalized/recipe]")
        if answer.lower() == "regionalized":
            impact_categories = [agb.findMethods('GWP_100a', mainCat='IPCC_AR6')[0],
                        agb.findMethods('GWP_100a', mainCat='IPCC_AR6')[1],
                        agb.findMethods('GWP_100a', mainCat='IPCC_AR6')[2],
                        agb.findMethods('GWP_100a', mainCat='IPCC_AR6')[3],
                        agb.findMethods('Particulate matter', mainCat='PM regionalized')[0],
                        agb.findMethods('Water stress', mainCat='AWARE regionalized')[0],
                        agb.findMethods('Occupation', mainCat='Biodiversity regionalized')[0],
                        agb.findMethods('Transformation', mainCat='Biodiversity regionalized')[0]]
            af_reg_name, ei_reg_name, bio_name = self.set_database_names_regionalized()
            self.check_databases(af_reg_name, ei_reg_name)
            value_chains_data = self.import_value_chains(file,sheet_name)
            self.analysis(ei_reg_name, af_reg_name, bio_name, value_chains_data, impact_categories)
        elif answer.lower() == "recipe":
            self.update_recipe_water_use(bio_name)
            impact_categories = [method for method in bd.methods if 'ReCiPe 2016 v1.03, midpoint (H) no LT' in method[0]]
            af_name, ei_name, bio_name = self.set_database_names()
            self.check_databases(af_name, ei_name)
            value_chains_data = self.import_value_chains(file,sheet_name)
            self.analysis(ei_name, af_name, bio_name, value_chains_data, impact_categories)
        else:
            print("Please enter either 'regionalized' or 'recipe'.")
            return

    @staticmethod
    def set_project_name():
        import bw2data as bd
        from ppplca.config import config

        bd.projects.dir
        project = config('project.name')
        bd.projects.set_current(project)
    
    @staticmethod
    def update_recipe_water_use(bio_name):
        import bw2data as bd

        bio3 = bd.Database(bio_name)
        method = [method for method in bd.methods if 'ReCiPe 2016 v1.03, midpoint (H) no LT' in method[0] and "water use no LT" in method[1] and "water consumption potential (WCP) no LT" in method[2]][0]
        m = bd.Method(method)
        cfs = m.load()

        water_use_list = [act for act in bio3 if "Water" in act['name']
                            and 'natural resource' in act['categories']
                            and 'air' not in act['name']
                            and 'ocean' not in act['name']
                            and 'ocean' not in act.get('categories')]
        water_emission_list = [act for act in bio3 if "Water" in act['name']
                                and 'water' in act['categories']
                                and 'ocean' not in act.get('categories')]

        existing_flows = {cf[0] for cf in cfs}

        for water_flow in water_use_list:
            if water_flow.key not in existing_flows:
                new_cf = (water_flow.key, 1)
                cfs.append(new_cf)
        for water_flow in water_emission_list:
            if water_flow.key not in existing_flows:
                new_cf = (water_flow.key, -1)
                cfs.append(new_cf)

        m.write(cfs)

    @staticmethod
    def set_database_names_regionalized():
        af_reg_name = "agrifootprint 6.3 all allocations_regionalized"
        ei_reg_name = "ecoinvent-3.10-cutoff_regionalized"
        bio_name = "ecoinvent-3.10-biosphere"

        return af_reg_name, ei_reg_name, bio_name
    
    @staticmethod
    def set_database_names():
        af_reg_name = "agrifootprint 6.3 all allocations"
        ei_reg_name = "ecoinvent-3.10-cutoff"
        bio_name = "ecoinvent-3.10-biosphere"

        return af_reg_name, ei_reg_name, bio_name
    
    @staticmethod
    def check_databases(af_name, ei_name):
        import bw2data as bd

        if ei_name in bd.databases and af_name in bd.databases:
            print(f"{ei_name} and {af_name} have already been imported.")
            
        else:
            print("Databases have not been imported yet. Please run script databases_setup.py first.")
            raise ValueError("Databases not found.")
    
    @staticmethod
    def import_value_chains(file, sheet_name = None):
        import pandas as pd

        if file == "value_chains_test.xlsx":
            value_chains_data = pd.read_excel(file, sheet_name='Value_chains')
        elif sheet_name:
            value_chains_data = pd.read_excel(file, sheet_name=sheet_name)
        else:
            value_chains_data = pd.read_excel(file, sheet_name=0)

        return value_chains_data
    
    def analysis(self, ei_reg_name, af_reg_name, bio_name, value_chains_data, impact_categories):
        import pandas as pd
        import lca_algebraic as agb
        from ppplca.Models.ValueChain import ValueChain
        from ppplca.Actions.CreateParams import CreateParams

        for _, value_chain_data in value_chains_data.iterrows():

            location_string = self.create_location_string(value_chain_data)

            ValueChain_ = ValueChain(value_chain_data['product'], location_string)

            #Load parametrized formulas
            name_formula_sheet = f"Formulas_{ValueChain_.product}"
            formulas = pd.read_excel("Processing_data.xlsx", sheet_name = name_formula_sheet)

            user_db = "ForegroundDB"
            agb.resetDb(user_db)
            agb.resetParams()

            print(f"Analysis for {ValueChain_.product} in locations {ValueChain_.location_string}.")

            CreateParams.createProcessParams(product=ValueChain_.product)
            params = agb.all_params()

            for i in range(1,len(value_chain_data),2):
                result = self.load_production_stages(i, value_chain_data, formulas, ValueChain_, ei_reg_name, af_reg_name, bio_name, user_db, params)
                if result is None:
                    continue
                else:
                    stage_name, stage, params = result
                ValueChain_.addStage(stage_name,stage)

            self.LCA_calculations(ValueChain_, params, user_db, impact_categories)

    @staticmethod
    def create_location_string(value_chain_data):
        locations = []
        processing_locations = []
        for i in range(1,len(value_chain_data),2):
            if value_chain_data.index.tolist()[i] == 'cultivation_country':
                locations.append(value_chain_data.iloc[i].split(" - ")[1])
            elif value_chain_data.index.tolist()[i] == 'pointofuse_country':
                locations.append(value_chain_data.iloc[i].split(" - ")[1])
            elif type(value_chain_data.iloc[i]) == str and value_chain_data.iloc[i].split(" - ")[1] not in processing_locations:
                locations.append(value_chain_data.iloc[i].split(" - ")[1])
                processing_locations.append(value_chain_data.iloc[i].split(" - ")[1])
        location_string = '-'.join(locations)

        return location_string
    
    @staticmethod
    def load_production_stages(i, value_chain_data, formulas, ValueChain_, ei_reg_name, af_reg_name, bio_name, user_db, params):
        import numpy as np
        from ppplca.Actions.CreateParams import CreateParams
        from ppplca.Models.ProductionStage import ProductionStage
        import lca_algebraic as agb

        if type(value_chain_data.iloc[i]) == float and np.isnan(value_chain_data.iloc[i]):
            return
        elif i == 1:
            stage_name = value_chain_data.index[i].split("_")[0]
            stage = ProductionStage(stage_name,value_chain_data.iloc[i],False,None)
        else:
            stage_name = value_chain_data.index[i].split("_")[0]
            previous_location = value_chain_data[:i][value_chain_data[:i].str.contains("-", na=False)].iloc[-1]
            if value_chain_data.iloc[i-1] == "Yes":
                stage = ProductionStage(stage_name,value_chain_data.iloc[i],True,previous_location)
                formula_transport_quantity = formulas[formulas["production_stage"] == stage_name].iloc[0]["formula"]
                stage.loadTransportExchanges()
                CreateParams.createTransportParams(stage,ValueChain_.crop_name_short)
                params = agb.all_params()
                stage.createTransportActivities(ei_reg_name,user_db,params,formula_transport_quantity)
            else:
                stage = ProductionStage(stage_name,value_chain_data.iloc[i],False,previous_location)
        if value_chain_data.index.tolist()[i] == 'cultivation_country':
            stage.loadAgriExchange()
        else:
            exchanges = formulas[formulas["production_stage"] == stage_name]
            stage.loadExchanges(exchanges)
        stage.loadActivities(ValueChain_.crop_name, ei_reg_name, af_reg_name, bio_name, user_db)
        print(f'Creating activity for {stage_name}.')
        stage.createForegroundActivities(user_db, params)

        return stage_name, stage, params
            
    @staticmethod
    def LCA_calculations(ValueChain_, params, user_db, impact_categories):
        import numpy as np
        import matplotlib
        matplotlib.use("Agg")
        from ppplca.config import config
        from ppplca.Models.LCA import LCA
            
        n_iterations = int(config('montecarlo.n_iterations'))
        np.random.seed(42)
        lca = LCA(impact_categories, params)
        lca.createParameterValues(n_iterations)
        lca.LCATotalInventory(user_db)
        lca.ContributionAnalysis(ValueChain_, n_iterations)
        lca.calculateSobolIndices()
        lca.exportResults(ValueChain_)