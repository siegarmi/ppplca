class CreateAgriActivities:

    @staticmethod
    def find_closest_cultivation_activity(production_location,crop_name):
        from pandas import read_csv
        
        distances_european_countries = read_csv("Data input/input_files/transport/Distances_european_countries_final.csv", sep = ";", decimal = ".")

        if crop_name == "Peas":
            production_countries = read_csv("Data input/input_files/production_countries/production_countries_pea_Europe.csv", sep = ";",header=None)[0].to_list()
        elif crop_name == "Soybeans":
            production_countries = read_csv("Data input/input_files/production_countries/production_countries_soy_Europe.csv", sep = ";",header=None)[0].to_list()
        else:
            production_countries = read_csv("Data input/input_files/production_countries/production_countries_wheat_Europe.csv", sep = ";",header=None)[0].to_list()

        mean_distances = []
        for country in production_countries:
            mean_distances.append(distances_european_countries.loc[(country[-2:] == distances_european_countries["country1 ID"]) & (production_location[-2:] == distances_european_countries["country2 ID"]) | (country[-2:] == distances_european_countries["country2 ID"]) & (production_location[-2:] == distances_european_countries["country1 ID"])]["mean"].iloc[0])
        closest_country = production_countries[mean_distances.index(min(mean_distances))]
        
        return closest_country
    
    @staticmethod
    def create(crop_name,cultivation_country,closest_country,process_type,eidb_reg,afdb_reg):
        """ for activity in [act for act in afdb_reg if "custom_agricultural_process_" in act["code"] and process_type in act['name'] and crop_name in act['name'] and "Economic" in act['name'] and "market" not in act['name'] and cultivation_country in act['location']]:
            activity.delete() """
        original_process = [act for act in afdb_reg if process_type in act['name'] and "green" not in act["name"] and crop_name in act['name'] and "Economic" in act['name'] and "market" not in act['name'] and closest_country[-2:] in act['location']][0]      
        new_process = original_process.copy(code="custom_agricultural_process_"+process_type+"_"+crop_name+"_"+cultivation_country,location=cultivation_country)
        new_process.save()
        new_process["name"] = original_process["name"].replace(closest_country[-2:],cultivation_country)
        new_process["reference product"] = original_process["reference product"].replace(closest_country[-2:],cultivation_country)
        new_process.save()
        
        for exchange in new_process.exchanges():
            if exchange["type"] == "technosphere":
                exchange_input_temp = [act for act in eidb_reg if act['code'] == exchange["input"][1]]
                if exchange_input_temp == []:
                    exchange_input = [act for act in afdb_reg if act['code'] == exchange["input"][1]][0]
                    process_in_ecoinvent = False
                else:
                    exchange_input = exchange_input_temp[0]
                    process_in_ecoinvent = True
                if exchange_input["location"] == closest_country[-2:]:
                    name = exchange["name"]
                    amount = exchange["amount"]
                    unit = exchange["unit"]
                    type = exchange["type"]
                    exchange.delete()
                    if process_in_ecoinvent:
                        exchange_substitution_temp = [act for act in eidb_reg if act['name'] == name and cultivation_country in act['location']]
                        if exchange_substitution_temp == []:
                            raise ValueError(name + " not available for "+cultivation_country+".")
                        else:
                            exchange_substitution = exchange_substitution_temp[0]
                    else:
                        name = exchange["name"].replace(closest_country[-2:],cultivation_country)
                        print(name)
                        exchange_substitution = [act for act in afdb_reg if act['name'] == name and cultivation_country in act['location']][0]
                    new_process.new_exchange(input=exchange_substitution.key, amount = amount, unit = unit, type = type).save()

        new_process.save()

    @classmethod
    def create_missing_agri_activities(cls,cultivation_country,crop_name,eidb_reg,afdb_reg):

        test_activity = [act for act in afdb_reg if "start material" in act['name'] and crop_name in act['name'] and "Economic" in act['name'] and "market" not in act['name'] and cultivation_country in act['location']]
        if test_activity == []:
            closest_country = cls.find_closest_cultivation_activity(cultivation_country,crop_name)
            print("Creating new agricultural activities for " + crop_name + " in " + cultivation_country + " based on the example of " + closest_country + ".")

            cls.create(crop_name,cultivation_country,closest_country,"start material",eidb_reg,afdb_reg)
            print("start material done")
            if crop_name == "Peas":
                cls.create(crop_name,cultivation_country,closest_country,"dry, at farm",eidb_reg,afdb_reg)
            elif crop_name == "Wheat":
                cls.create(crop_name,cultivation_country,closest_country,"grain, at farm",eidb_reg,afdb_reg)
            else:
                cls.create(crop_name,cultivation_country,closest_country,"at farm",eidb_reg,afdb_reg)
            cls.create(crop_name,cultivation_country,closest_country,"dried",eidb_reg,afdb_reg)
        else:
            print("Agricultural activities for " + crop_name + " in " + cultivation_country + " are already present.")
