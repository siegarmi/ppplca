class LCAResults:
    def __init__(self):
        self.overall = {}
        self.contribution_analysis = {}
        self.contribution_analysis_cleaned = {}
        self.contribution_analysis_mean = None
        self.overall_impacts = None
        self.overall_impacts_protein = None
        self.sobol = {}
        self.sobol_total = {}
        self.sobol_harmonized = []
        self.sobol_total_harmonized = []

    def loadResults(self, file_name, result_type):
        import pandas as pd

        file_name_no_csv = file_name.split(".")[0]
        file_name_parts = file_name_no_csv.split("_")
        country_names = file_name_parts[1].split("-")

        if result_type == "overall":
            if file_name_parts[-1] == "protein":
                self.overall[f'{file_name_parts[0]}_{country_names[0]}-{country_names[1]}_{file_name_parts[-1]}'] = pd.read_csv(f'Parametrized_LCA_results/{file_name}',index_col=[0])
            else:
                self.overall[f'{file_name_parts[0]}_{country_names[0]}-{country_names[1]}'] = pd.read_csv(f'Parametrized_LCA_results/{file_name}',index_col=[0])
        elif result_type == "contribution_analysis":
            self.contribution_analysis[f'{file_name_parts[0]}_{country_names[0]}-{country_names[1]}'] = pd.read_csv(f'Parametrized_LCA_results/{file_name}',index_col=[0])
        elif result_type == "sobol":
            if file_name_parts[-1] == "total":
                self.sobol_total[f'{file_name_parts[0]}_{country_names[0]}-{country_names[1]}_{file_name_parts[-1]}'] = pd.read_csv(f'Parametrized_LCA_results/{file_name}',index_col=[0])
            else:
                self.sobol[f'{file_name_parts[0]}_{country_names[0]}-{country_names[1]}'] = pd.read_csv(f'Parametrized_LCA_results/{file_name}',index_col=[0])

    def loadContributionAnalysisResults(self, file_name):
        import pandas as pd

        file_name_no_csv = file_name.split(".")[0]
        file_name_parts = file_name_no_csv.split("_")
        country_names = file_name_parts[1].split("-")

        self.contribution_analysis[f'{file_name_parts[0]}_{country_names[0]}-{country_names[1]}'] = pd.read_csv(f'Parametrized_LCA_results/{file_name}',index_col=[0])

    def sortResults(self, result_type):
        sort_term = ["gluten", "SPI", "SPC", "PPI", "PPC"]

        def get_priority_group(key):
            for i, word in enumerate(sort_term):
                if word in key:
                    return i
            return len(sort_term)

        if result_type == "overall":
            sorted_results = sorted(self.overall.items(), key=lambda item: get_priority_group(item[0]))
            self.overall = dict(sorted_results)
        elif result_type == "contribution_analysis":
            sorted_results = sorted(self.contribution_analysis.items(), key=lambda item: get_priority_group(item[0]))
            self.contribution_analysis = dict(sorted_results)

    def summarizeoverallImpacts(self):
        GWP_impacts = []
        PM25_impacts = []
        WU_impacts = []
        LU_impacts = []
        GWP_impacts_protein = []
        PM25_impacts_protein = []
        WU_impacts_protein = []
        LU_impacts_protein = []

        def format_impact_data(df,GWP_impacts,PM25_impacts,WU_impacts,LU_impacts):
            GWP_impacts.append(list(df["GWP_100a - all[CO2-eq]"]))
            PM25_impacts.append(list(df["Particulate matter - health impacts (PMHI)[DALY]"]))
            WU_impacts.append(list(df["Water stress - Annual[m3 world]"]))
            Sum_LU_impacts = [x + y for x, y in zip(list(df["Occupation - Biodiversity loss (LUBL)[PDF*year/m2a]"]),list(df["Transformation - Biodiversity loss (LUBL)[PDF*year/m2]"]))]
            LU_impacts.append(Sum_LU_impacts)
            return GWP_impacts, PM25_impacts, WU_impacts, LU_impacts

        for key, df in self.overall.items():
            if "protein" in key:
                GWP_impacts_protein, PM25_impacts_protein, WU_impacts_protein, LU_impacts_protein = format_impact_data(df,GWP_impacts_protein, PM25_impacts_protein, WU_impacts_protein, LU_impacts_protein)
            else:
                GWP_impacts, PM25_impacts, WU_impacts, LU_impacts = format_impact_data(df,GWP_impacts, PM25_impacts, WU_impacts, LU_impacts)

        self.overall_impacts = [GWP_impacts,PM25_impacts,WU_impacts,LU_impacts]
        self.overall_impacts_protein = [GWP_impacts_protein, PM25_impacts_protein, WU_impacts_protein, LU_impacts_protein]
    
    @staticmethod
    def clean_and_sort_dataframe(df):
        #Define processes and impacts in the desired order
        processes = [
            'cultivation', 'dehulling', 'milling', 'defatting', 'extraction',
            'heat_extraction', 'electricity_extraction', 'transport'
        ]

        impact_order = [
            "GWP_100a - all[CO2-eq]",
            "Particulate matter - health impacts (PMHI)[DALY]",
            "Water stress - Annual[m3 world]",
            "Total - Biodiversity loss (LUBL)[PDF]"
        ]

        #Drop unwanted impact types
        drop_impacts = [
            "GWP_100a - Biogenic[CO2-eq]",
            "GWP_100a - Fossil[CO2-eq]",
            "GWP_100a - LUC[CO2-eq]"
        ]
        df = df.drop(columns=[col for col in df.columns if any(imp in col for imp in drop_impacts)], errors='ignore')

        #Drop pointofuse columns
        df = df.drop(columns=[col for col in df.columns if "pointofuse" in col])

        #Calculate total biodiversity loss per process
        for process in processes:
            occ_col = f"{process} - Occupation - Biodiversity loss (LUBL)[PDF*year/m2a]"
            trans_col = f"{process} - Transformation - Biodiversity loss (LUBL)[PDF*year/m2]"
            total_col = f"{process} - Total - Biodiversity loss (LUBL)[PDF]"

            if occ_col in df.columns and trans_col in df.columns:
                df[total_col] = df[occ_col] + df[trans_col]
                df = df.drop(columns=[occ_col, trans_col])

        #Add missing columns filled with 0
        for process in processes:
            for impact in impact_order:
                col_name = f"{process} - {impact}"
                if col_name not in df.columns:
                    df[col_name] = 0.0

        #Sort columns by process and impact
        sorted_columns = []
        for impact in impact_order:
            for proc in processes:
                sorted_columns.append(f"{proc} - {impact}")

        df = df[sorted_columns]

        impact_rename_map = {
            "GWP_100a - all[CO2-eq]": "GWP",
            "Particulate matter - health impacts (PMHI)[DALY]": "PMHI",
            "Water stress - Annual[m3 world]": "WS",
            "Total - Biodiversity loss (LUBL)[PDF]": "LUBL"
        }

        new_columns = []
        for col in df.columns:
            process, impact = col.split(" - ", 1)
            short_impact = impact_rename_map.get(impact, impact)
            new_columns.append(f"{process} - {short_impact}")

        df.columns = new_columns

        return df
        

    def cleanContributionAnalysisResults(self):
        for key, df in self.contribution_analysis.items():
            self.contribution_analysis_cleaned[key] = self.clean_and_sort_dataframe(df)
        
    def calculateMeanContribution(self):
        import pandas as pd

        all_rows = []
        for key, df in self.contribution_analysis_cleaned.items():
            mean_values = df.mean()
            all_rows.append(pd.DataFrame([mean_values], index=[key]))
        combined_means = pd.concat(all_rows)
        self.contribution_analysis_mean = combined_means.fillna(0)
    
    @staticmethod
    def splitDicts(sobol_dict):
        products = ["gluten", "SPI", "SPC", "PPI", "PPC"]
        sobols_by_product = []
        for product in products:
            sobols_by_product.append({k: v for k, v in sobol_dict.items() if product in k})

        return sobols_by_product
    
    @staticmethod
    def align(sobols_by_product):
        sobols_aligned = []
        for sobols in sobols_by_product:
            all_indices = set()
            for sobol_df in sobols.values():
                all_indices.update(sobol_df.index)
            all_indices = sorted(all_indices)

            # Step 2: Reindex each DataFrame, filling missing rows with 0
            aligned_sobol_dict = {}
            for key, sobol_df in sobols.items():
                aligned_sobol_df = sobol_df.reindex(all_indices).fillna(0)
                aligned_sobol_dict[key] = aligned_sobol_df

            sobols_aligned.append(aligned_sobol_dict)

        return sobols_aligned
    
    @staticmethod
    def sum_transport_and_biodiversity_impacts(sobols):
        import pandas as pd

        result_dict = {}

        for key, df in sobols.items():
            # Identify transport-related rows
            transport_mask = df.index.str.contains("transport", case=False)

            # Sum those rows into one row
            transport_sum = df[transport_mask].sum(axis=0)

            # Drop transport-related rows
            df_cleaned = df[~transport_mask]

            # Add the new "Transport distances" summary row
            transport_row = pd.DataFrame([transport_sum], index=["Transport distances"])

            # Append and return
            df_result = pd.concat([df_cleaned, transport_row])

            # Sum biodiversity loss from occupation and transformation
            df_result["('Biodiversity regionalized','Total','Biodiversity loss (LUBL)')"] = (df_result["('Biodiversity regionalized', 'Occupation', 'Biodiversity loss (LUBL)')"] + df_result["('Biodiversity regionalized', 'Transformation', 'Biodiversity loss (LUBL)')"]) / 2 #divided by two since the two biodiversity columns are added --> values would add up to 2 instead of 1
            df_result.drop(columns=["('IPCC_AR6', 'GWP_100a', 'Biogenic')","('IPCC_AR6', 'GWP_100a', 'Fossil')","('IPCC_AR6', 'GWP_100a', 'LUC')","('Biodiversity regionalized', 'Occupation', 'Biodiversity loss (LUBL)')","('Biodiversity regionalized', 'Transformation', 'Biodiversity loss (LUBL)')"], inplace = True)

            result_dict[key] = df_result

        return result_dict
    
    def harmonizeSobolResults(self):

        if self.sobol:
            sobols_by_product = self.splitDicts(self.sobol)
            sobols_by_product_aligned = self.align(sobols_by_product)
            for sobols in sobols_by_product_aligned:
                self.sobol_harmonized.append(self.sum_transport_and_biodiversity_impacts(sobols))
        if self.sobol_total:
            sobols_total_by_product = self.splitDicts(self.sobol_total)
            sobols_total_by_product_aligned = self.align(sobols_total_by_product)
            for sobols_total in sobols_total_by_product_aligned:
                self.sobol_total_harmonized.append(self.sum_transport_and_biodiversity_impacts(sobols_total))