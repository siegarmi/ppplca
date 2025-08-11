class LCA:
    def __init__(self, impact_categories, params):
        self.impact_categories = impact_categories
        self.parameters = params
        self.parameter_values = {}
        self.total_inventory = None
        self.results_contribution_temp = {}
        self.results_contribution = {}
        self.results_contribution_protein = {}
        self.results_overall = {}
        self.results_overall_protein = {}
        self.sobol_indices = None
        self.sobol_indices_total = None

    def createParameterValues(self, n_iterations):
        import lca_algebraic as agb
        import numpy as np

        for param in self.parameters:
            if self.parameters[param].distrib == "fixed":
                self.parameter_values[param] = np.array([self.parameters[param].default] * n_iterations)
            else:
                random_array = np.random.rand(1,n_iterations)[0]
                self.parameter_values[param] = np.array(self.parameters[param].rand(random_array))
    
    def getParameterValues(self):
        import pandas as pd

        df = pd.DataFrame(self.parameter_values)

        return df
    
    def LCAcontributionAnalysis(self, ValueChain, n_iterations):
        import lca_algebraic as agb
        import pandas as pd
        import numpy as np

        input_amounts = ['1']
        params = self.parameters #required by the eval() function

        for _, production_stage in reversed(list(ValueChain.production_stages.items())[1:]):
            print(production_stage.name)

            for exchange in production_stage.exchanges:
                print(exchange.name)
                if "input" in exchange.name and "allocation" not in exchange.name or "transport" in exchange.name:
                    if "input" in exchange.name:
                        input_amounts.append(exchange.formula)
                        activity_key = exchange.name.split("_")[1]
                    else:
                        activity_key = exchange.name
                    reference_flow_formula = "*".join(input_amounts)
                    reference_flow = 1/eval(reference_flow_formula)
                    activity = production_stage.activities[activity_key].object
                    activity_name = production_stage.activities[activity_key].name

                    self.results_contribution_temp[activity_name] = agb.compute_impacts(
                        activity,
                        self.impact_categories,
                        functional_unit=reference_flow,
                        **self.parameter_values)
                    self.results_contribution_temp[activity_name] = self.results_contribution_temp[activity_name].reset_index(drop=True)

        try:
            extraction_electricity_activity = ValueChain.production_stages["extraction"].activities["electricity_mix"].object
            electricity_input_formula = [exc for exc in ValueChain.production_stages["extraction"].exchanges if exc.name == "electricity_mix"][0].formula
            allocation_formula = [exc for exc in ValueChain.production_stages["extraction"].exchanges if exc.name == "extraction_allocation"][0].formula
            functional_value = 1/eval(electricity_input_formula + "*" + allocation_formula)

            self.results_contribution_temp["electricity_extraction"] = agb.compute_impacts(
                extraction_electricity_activity,
                self.impact_categories,
                functional_unit=functional_value,
                **self.parameter_values)
            self.results_contribution_temp["electricity_extraction"] = self.results_contribution_temp["electricity_extraction"].reset_index(drop=True)
        except (IndexError, KeyError):
            print("No electricity used in extraction or no extraction step modelled.")
            self.results_contribution_temp["electricity_extraction"] = pd.DataFrame({"GWP_100a - all[CO2-eq]": np.zeros(n_iterations), "GWP_100a - Biogenic[CO2-eq]": np.zeros(n_iterations), "GWP_100a - Fossil[CO2-eq]": np.zeros(n_iterations), "GWP_100a - LUC[CO2-eq]": np.zeros(n_iterations), "Particulate matter - health impacts (PMHI)[DALY]":np.zeros(n_iterations), "Water stress - Annual[m3 world]":np.zeros(n_iterations), "Occupation - Biodiversity loss (LUBL)[PDF*year/m2a]":np.zeros(n_iterations) , "Transformation - Biodiversity loss (LUBL)[PDF*year/m2]":np.zeros(n_iterations)})

        try:
            extraction_heat_activity = ValueChain.production_stages["extraction"].activities["heat_mix"].object
            heat_input_formula = [exc for exc in ValueChain.production_stages["extraction"].exchanges if exc.name == "heat_mix"][0].formula
            allocation_formula = [exc for exc in ValueChain.production_stages["extraction"].exchanges if exc.name == "extraction_allocation"][0].formula
            functional_value = 1/eval(heat_input_formula + "*" + allocation_formula)

            self.results_contribution_temp["heat_extraction"] = agb.compute_impacts(
                    extraction_heat_activity,
                    self.impact_categories,
                    functional_unit=functional_value,
                    **self.parameter_values)
            self.results_contribution_temp["heat_extraction"] = self.results_contribution_temp["heat_extraction"].reset_index(drop=True)
        
        except (IndexError, KeyError):
            print("No heat used in extraction or no extraction step modelled.")
            self.results_contribution_temp["heat_extraction"] = pd.DataFrame({"GWP_100a - all[CO2-eq]": np.zeros(n_iterations), "GWP_100a - Biogenic[CO2-eq]": np.zeros(n_iterations), "GWP_100a - Fossil[CO2-eq]": np.zeros(n_iterations), "GWP_100a - LUC[CO2-eq]": np.zeros(n_iterations), "Particulate matter - health impacts (PMHI)[DALY]":np.zeros(n_iterations), "Water stress - Annual[m3 world]":np.zeros(n_iterations), "Occupation - Biodiversity loss (LUBL)[PDF*year/m2a]":np.zeros(n_iterations) , "Transformation - Biodiversity loss (LUBL)[PDF*year/m2]":np.zeros(n_iterations)})

        name_last_process = list(ValueChain.production_stages.items())[-1][0]
        print(name_last_process)
        self.results_contribution_temp[name_last_process] = self.results_overall

    def calculateContributionResults(self):
        
        process_order = ["cultivation", "dehulling", "milling", "defatting", "extraction", "pointofuse"]
        order_index = {k: i for i, k in enumerate(process_order)}
        self.results_contribution_temp = dict(sorted(self.results_contribution_temp.items(), key=lambda item: order_index.get(item[0], float('inf'))))

        previous_process_key = None
        first_transport_process = True
        for key, process in self.results_contribution_temp.items():
            if not previous_process_key or key == "electricity_extraction" or key == "heat_extraction":
                for impact_category in process.columns:
                    self.results_contribution[f'{key} - {impact_category}'] = process[impact_category]
            elif key == "extraction":
                for impact_category in process.columns:
                    self.results_contribution[f'{key} - {impact_category}'] = process[impact_category] - self.results_contribution_temp[previous_process_key][impact_category]
                    try:
                        self.results_contribution[f'{key} - {impact_category}'] = self.results_contribution[f'{key} - {impact_category}'] - self.results_contribution_temp["electricity_extraction"][impact_category]
                    except KeyError:
                        pass
                    try:
                        self.results_contribution[f'{key} - {impact_category}'] = self.results_contribution[f'{key} - {impact_category}'] - self.results_contribution_temp["heat_extraction"][impact_category]
                    except KeyError:
                        pass
            elif "transport" in key:
                production_process_key = key.split("_")[0]
                for impact_category in process.columns:
                    self.results_contribution[f'{production_process_key} - {impact_category}'] = self.results_contribution[f'{production_process_key} - {impact_category}'] - process[impact_category]

                if first_transport_process:
                    first_transport_process = False
                    for impact_category in process.columns:
                        self.results_contribution[f'transport - {impact_category}'] = process[impact_category]
                else:
                    for impact_category in process.columns:
                        self.results_contribution[f'transport - {impact_category}'] = self.results_contribution[f'transport - {impact_category}'] + process[impact_category]
            else:
                for impact_category in process.columns:
                    self.results_contribution[f'{key} - {impact_category}'] = process[impact_category] - self.results_contribution_temp[previous_process_key][impact_category]
            previous_process_key = key

        protein_content_extract = next(v for k, v in self.parameter_values.items() if "protein_out" in k)
        self.results_contribution_protein = self.results_contribution.copy()
        for process in self.results_contribution_protein:
            self.results_contribution_protein[process] = self.results_contribution_protein[process] / protein_content_extract

    def ContributionAnalysis(self, ValueChain, n_iterations):
        self.LCAcontributionAnalysis(ValueChain, n_iterations)
        self.calculateContributionResults()

    def getContributionResults(self):
        import pandas as pd

        res = pd.DataFrame(self.results_contribution)
        res_protein = pd.DataFrame(self.results_contribution_protein)
        

        return res, res_protein
    
    def LCATotalInventory(self, user_db):
        import lca_algebraic as agb
        import bw2data as bd
        
        functional_value = 1
        params = self.parameter_values #required by the eval() function

        process_order = ["cultivation", "dehulling", "milling", "defatting", "extraction", "pointofuse"]
        process_activities = [act for act in bd.Database(user_db) if act["name"] in process_order]
        order_index = {name: i for i, name in enumerate(process_order)}
        process_activities.sort(key=lambda act: order_index.get(act["name"], float('inf')))
        self.total_inventory = process_activities[-1]
        self.results_overall = agb.compute_impacts(
        self.total_inventory,
        self.impact_categories,
        functional_unit=functional_value,
        **self.parameter_values)
        self.results_overall = self.results_overall.reset_index(drop=True)
        
        protein_content_extract = next(v for k, v in self.parameter_values.items() if "protein_out" in k)

        self.results_overall_protein = self.results_overall.copy()
        self.results_overall_protein = self.results_overall_protein.div(protein_content_extract, axis=0)

        self.results_overall.to_csv(f"Parametrized_LCA_results/test.csv",index=True)


    def calculateSobolIndices(self):
        import lca_algebraic as agb
        import pandas as pd

        functional_value = 1

        oat_matrix = agb.oat_matrix(
            self.total_inventory,
            self.impact_categories,
            functional_unit=functional_value)

        sobol_indices = agb.incer_stochastic_matrix(
            self.total_inventory,
            self.impact_categories,
            functional_unit=functional_value)

        oat_matrix.index.tolist()
        self.sobol_indices = pd.DataFrame(sobol_indices.s1,columns = self.impact_categories, index = oat_matrix.index.tolist())
        self.sobol_indices_total = pd.DataFrame(sobol_indices.st,columns = self.impact_categories, index = oat_matrix.index.tolist())

    def exportResults(self, ValueChain):
        self.results_overall.to_csv(f"Parametrized_LCA_results/{ValueChain.product}_{ValueChain.location_string}_results_overall.csv",index=True)
        self.results_overall_protein.to_csv(f"Parametrized_LCA_results/{ValueChain.product}_{ValueChain.location_string}_results_overall_protein.csv",index=True)

        res_contribution, res_contribution_protein = self.getContributionResults()
        res_contribution.to_csv(f"Parametrized_LCA_results/{ValueChain.product}_{ValueChain.location_string}_results_contribution_analysis.csv", index=True)
        res_contribution_protein.to_csv(f"Parametrized_LCA_results/{ValueChain.product}_{ValueChain.location_string}_results_contribution_analysis_protein.csv", index=True)

        self.getParameterValues().to_csv(f"Parametrized_LCA_results/{ValueChain.product}_{ValueChain.location_string}_parameter_values.csv", index=True)

        self.sobol_indices.to_csv(f"Parametrized_LCA_results/{ValueChain.product}_{ValueChain.location_string}_sobol_indices.csv", index=True)
        self.sobol_indices_total.to_csv(f"Parametrized_LCA_results/{ValueChain.product}_{ValueChain.location_string}_sobol_indices_total.csv", index=True)