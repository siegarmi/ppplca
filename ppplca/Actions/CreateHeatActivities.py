class CreateHeatActivities:

    @classmethod
    def create_heat_production_process(cls,country,crop_name,eidb_reg):
        from ppplca.Actions.FindActivityLocation import FindActivityLocation
        import bw2data as bd

        """ for activity in [act for act in eidb_reg if "custom_heat_process_" + str(country) + "_" + str(crop_name) in act['code'] and country in act['location']]:
            activity.delete() """

        original_process = [act for act in eidb_reg if act['name'] == "heat production, natural gas, at boiler modulating >100kW" and "CA-QC" in act['location']][0]
        new_activity = original_process.copy(code="custom_heat_process_"+country+"_"+crop_name,name=original_process["name"],location=country)
        new_activity.save()

        for exchange in new_activity.exchanges():
            code = exchange["input"][1]
            db = exchange["input"][0]
            input_act = [act for act in bd.Database(db) if act["code"] == code][0]
            if input_act.get("location"):
                if exchange["type"] != "production" and (input_act["location"] == "CA-QC" or input_act["location"] == "CA"):
                    amount = exchange["amount"]
                    unit = exchange["unit"]
                    type = exchange["type"]
                    exchange.delete()
                    exchange_substitution_temp = [act for act in bd.Database(db) if act['name'] == input_act["name"] and act['location'] == country]
                    exchange_substitution_temp = FindActivityLocation.find(exchange_substitution_temp,input_act["name"],country,crop_name,bd.Database(db))
                    exchange_substitution = exchange_substitution_temp[0]
                    new_activity.new_exchange(input=exchange_substitution.key, amount = amount, unit = unit, type = type).save()
            
        new_activity.save()