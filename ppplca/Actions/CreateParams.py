class CreateParams:
    
    @staticmethod
    def create(name,distribution,minimum,maximum,mean,sd):
        import lca_algebraic as agb
        if distribution == "TRIANGLE":
            param = agb.newFloatParam(
                name,
                default=float(mean),
                min=float(minimum),
                max=float(maximum),
                distrib=agb.DistributionType.TRIANGLE,
                description=name)
        elif distribution == "FIXED":
            param = agb.newFloatParam(
                name,
                default=float(mean),
                distrib=agb.DistributionType.FIXED,
                description=name)
        elif distribution == "NORMAL":
            param = agb.newFloatParam(
                name,
                default=float(mean),
                min=float(minimum),
                max=float(maximum),
                std=float(sd),
                distrib=agb.DistributionType.NORMAL,
                description=name)
        elif distribution == "LOGNORMAL":
            param = agb.newFloatParam(
                name,
                default=float(mean),
                std=float(sd),
                min=float(minimum),
                max=float(maximum),
                distrib=agb.DistributionType.LOGNORMAL,
                description=name)
        elif distribution == "UNIFORM":
            param = agb.newFloatParam(
                name,
                default=(float(minimum)+float(maximum))/2,
                std=float(sd),
                min=float(minimum),
                max=float(maximum),
                distrib=agb.DistributionType.LINEAR,
                description=name)
        else:
            raise ValueError("Selected distribution type doesn't exist.")
    
    @classmethod
    def createProcessParams(cls, product):
        from pandas import read_excel
        import lca_algebraic as agb

        input_parameters = read_excel('Data input/value_chains_and_processing_data/Processing_data.xlsx', sheet_name='General_parameters')
        input_parameters_selected = input_parameters[input_parameters.iloc[:, 0] == product]
        input_parameters_selected = input_parameters_selected.reset_index(drop=True)

        for i in range(0,len(input_parameters_selected)):
            cls.create(name=input_parameters_selected.iloc[i]["name"],
                       distribution=input_parameters_selected.iloc[i]["distribution"],
                       minimum=input_parameters_selected.iloc[i]["min"],
                       maximum=input_parameters_selected.iloc[i]["max"],
                       mean=input_parameters_selected.iloc[i]["mean"],
                       sd=input_parameters_selected.iloc[i]["sd"])

    @classmethod
    def createTransportParams(cls, production_stage, crop_name):
        from pandas import read_csv
        from numpy import nan
        import lca_algebraic as agb

        distances_european_countries = read_csv(f"Data input/input_files/transport/Distances_european_countries_final.csv", sep = ";", decimal = ".")
        production_to_port_distance = read_csv(f"Data input/input_files/transport/Production_to_port_distance.csv", sep = ";", decimal = ".")
        transport_between_ports = read_csv(f"Data input/input_files/transport/Transport_between_ports.csv", sep = ";", decimal = ".")
        europe_distance_from_port = read_csv(f"Data input/input_files/transport/Europe_distance_from_port.csv", sep = ";", decimal = ".")

        params = []

        def add_param(suffix, mean, sd, detour_factor = 1):
            params.append({
                "name": f"{production_stage.name}_{suffix}",
                "mean": mean * detour_factor,
                "sd": sd * detour_factor
            })

        if production_stage.country.isinEurope() and production_stage.country_last_production_stage.isinEurope():
            target_country_ids = {production_stage.country.iso2,production_stage.country_last_production_stage.iso2}
            row = distances_european_countries[distances_european_countries.apply(lambda row: {row["country1 ID"], row["country2 ID"]} == target_country_ids, axis=1)].iloc[0]
            add_param("transport_europe", float(row["mean"]), float(row["sd"]), detour_factor= 1.2)  # Detour factor 1.2 to translate air distance to road distance
            
        else:
            row = production_to_port_distance.query(
                "Crop == @crop_name and `Country ID` == @production_stage.country_last_production_stage.iso2"
            ).iloc[0]
            add_param("transport_overseas", float(row["mean"]), float(row["sd"]), detour_factor=1.2)  # Detour factor 1.2 to translate air distance to road distance

            row = transport_between_ports.query(
                "Crop == @crop_name and `Origin ID` == @production_stage.country_last_production_stage.iso2 and `Destination ID` == @production_stage.country.iso2"
            ).iloc[0]
            add_param("transport_shipping", float(row["mean"]), float(row["sd"]))
            
            row = europe_distance_from_port.query("ID == @production_stage.country.iso2").iloc[0]
            add_param("transport_europe_port", float(row["mean"]), float(row["sd"]), detour_factor=1.2)  # Detour factor 1.2 to translate air distance to road distance

        for param in params:
            cls.create(
                name=param["name"], 
                distribution="NORMAL", 
                minimum=1e-6, #cannot be 0.0 otherwise if statement in lca_algebraic function rand does yield None
                maximum=1e6, #very large number because if max = nan, all values of the truncated normal distribution yield nan
                mean=param["mean"],
                sd=param["sd"]
            )