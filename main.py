import numpy as np
import pandas as pd
import bw2data as bd
import lca_algebraic as agb

from ppplca.config import config
from ppplca.Models.ProductionStage import ProductionStage
from ppplca.Models.ValueChain import ValueChain
from ppplca.Actions.CreateParams import CreateParams
from ppplca.Models.LCA import LCA

bd.projects.dir
#Setting project name
project = config('project.name')
bd.projects.set_current(project)

#define names of databases
af_reg_name = "agrifootprint 6.3 all allocations_regionalized"
ei_reg_name = "ecoinvent-3.10-cutoff_regionalized"
bio_name = "ecoinvent-3.10-biosphere"

#Check if databases have been imported
if ei_reg_name in bd.databases and af_reg_name in bd.databases:
    eidb_reg = bd.Database(ei_reg_name)
    afdb_reg = bd.Database(af_reg_name)
    print(ei_reg_name + " and " + af_reg_name + " have already been imported.")
else:
    print("Databases have not been imported yet. Please run script databases_setup.py first.")

#Import information about value chains
value_chains_data = pd.read_excel('Data input/value_chains_and_processing_data/value_chains_test.xlsx', sheet_name='Value_chains')

#Iterate through the different value chains to conduct the analysis
for _, value_chain_data in value_chains_data.iterrows():

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
    #Create value chain object  
    ValueChain_ = ValueChain(value_chain_data['product'], location_string)

    #Load parametrized formulas
    name_formula_sheet = f"Formulas_{ValueChain_.product}"
    formulas = pd.read_excel("Data input/value_chains_and_processing_data/Processing_data.xlsx", sheet_name = name_formula_sheet)

    user_db = "ForegroundDB"
    agb.resetDb(user_db)
    agb.resetParams()

    print(f"Analysis for {ValueChain_.product} in locations {ValueChain_.location_string}.")

    #Create parameters for the value chain
    CreateParams.createProcessParams(product=ValueChain_.product)
    params = agb.all_params()

    #Load and create activities for value chain
    for i in range(1,len(value_chain_data),2):
        if type(value_chain_data.iloc[i]) == float and np.isnan(value_chain_data.iloc[i]):
            continue
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
        ValueChain_.addStage(stage_name,stage)
    
    #LCA
    #Impact categories can be changed manually
    impact_categories = [agb.findMethods('GWP_100a', mainCat='IPCC_AR6')[0],
                    agb.findMethods('GWP_100a', mainCat='IPCC_AR6')[1],
                    agb.findMethods('GWP_100a', mainCat='IPCC_AR6')[2],
                    agb.findMethods('GWP_100a', mainCat='IPCC_AR6')[3],
                    agb.findMethods('Particulate matter', mainCat='PM regionalized')[0],
                    agb.findMethods('Water stress', mainCat='AWARE regionalized')[0],
                    agb.findMethods('Occupation', mainCat='Biodiversity regionalized')[0],
                    agb.findMethods('Transformation', mainCat='Biodiversity regionalized')[0]]    
    n_iterations = int(config('montecarlo.n_iterations'))
    np.random.seed(42)
    lca = LCA(impact_categories, params)
    lca.createParameterValues(n_iterations)
    lca.LCATotalInventory(user_db)
    lca.ContributionAnalysis(ValueChain_, n_iterations)
    lca.calculateSobolIndices()
    lca.exportResults(ValueChain_)