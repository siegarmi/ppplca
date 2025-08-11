# ppplca (parametric plant protein life cycle assessment)

This repository contains the model code and required input data files for parametric LCAs of plant protein value chains based on variable process parameters and geographical locations.

## Requirements

- [ecoinvent](https://ecoinvent.org/) license (username & password)
- [Agrifootprint](https://blonksustainability.nl/agri-footprint) v6.3 database in a Simapro.csv format
- python >=3.12

## Install 

```bash
pip install ppplca
```

## Run

In the project folder run:
```python
import ppplca

ppplca.install()
```
This creates all the necessary sub-folders in the project folder, loads the config.ini file, the excel file containing the process parameters, the excel file to define the value chains that should be calculated, and asks you to locate the agrifootprint database to store it in the created Database folder.

After defining the parameters in the config.ini file, choosing the value chains, and optionally changing parameter values, run:
```python
ppplca.setup()
```
This sets up a brightway2 project, loads and links the econivent and agrifootprint databases, regionalizes them, and creates necessary processes such as cultivation, electricity mixes, and heat production. The regionalization of the databases can take up to 48 hours on a regular laptop.

After the setup is finished, run:
```python
ppplca.run()
```
or if you want to select your own excel file to specify the value chains:
```python
ppplca.run('filename.xlsx', sheet=None)
# filename.xlsx must be located in working directory
# The first sheet will be loaded for analysis unless specified either by number or worksheet name.
```

This yields environmental impacts (see below for more details) for the defined value chains based on multiple Monte-Carlo simulations or single runs depending on the value defined in config.ini. They are stored in the folder Parametrized_LCA_results. Specifically, it provides the following files for each value chain:
- Overall results for each Monte-Carlo iteration based on 1 kg product
- Overall results for each Monte-Carlo iteration based on 1 kg protein
- Contribution analysis based on 1 kg product
- Contribution analysis based on 1 kg protein
- First order Sobol-indices (global sensitivity analysis)
- Total Sobol-indices
- Parameter values for each iteration

## The model

Currently, the model is designed to calculate environmental impacts for the value chains of pea protein isolate (PPI) and concentrate (PPC), soy protein isolate (SPI) and concentrate (SPC), and wheat gluten (WG).

### System boundaries

They system boundaries can be chosen flexibly based on the following processes:
- Cultivation
- Pre-treatment
- Milling
- Defatting
- Protein extraction (Various technologies)
- Transport between processes and until point-of-use.

### Geographical scope

The geographical scope includes all European countries for the processing steps. Countries for cultivation are principally limited by the coverage of the Agrifootprint database. However, there is a function implemented that creates cultivation processes based on the closest available country in the Agrifootprint database by adapting, e.g., electricity mixes but not local conditions such as the availability of peat soils. Additionally, the US is available for the cultivation and processing of soy and wheat, Brazil for the cultivation and processing of soy, and China for the cultivation and processing of pea, soy, and wheat. For processing in Brazil, China, or the US no transport between the cultivation and processing facility can be modelled currently (assumption that it is nearby or on the way to the port).

### Functional units

Currently, a mass- and protein-based functional are used. Variable protein contents in the final product are considered when using a protein-based functional unit

### Multi-functionality

Currently, multi-functionality of processes is dealt with by economic allocation (but any allocation type possible). The uncertainty of allocation factors can be taken into account in the models.

### Impact assessment

Currently, the model calculates environmental impacts based on regional characterization factors for water stress, land use related biodiversity loss, and particulate matter related human health impacts. For climate change, the factors from IPCC are used. However, any other impact assessment can be added to the model

## Model dependencies

The model is based on the [Brightway 2](https://github.com/brightway-lca/brightway2) library and [lca_algebraic](https://github.com/oie-mines-paristech/lca_algebraic/).

The code for loading the agrifootprint database and regionalizing the databases is based on work of [Jing et al. (2024)](https://doi.org/10.1021/acs.est.4c03005).

The regionalization further required input data from [Scherer et al. (2023)](https://doi.org/10.1021/acs.est.3c04191), [Boulay et al. (2018)](https://doi.org/10.1007/s11367-017-1333-8), and [Oberschelp et al. (2020)](https://dx.doi.org/10.1021/acs.est.0c05691).

## Possible adjustments of the model for further applications

1. Use different cultivation activities instead of the ones provided in the Agrifootprint database to cover more countries, increase the resolution to a sub-country level, or investigate different cultivation practices deviating from the average cultivation.

2. Expand the transport to other countries apart from Europe and the production locations in Brazil, China, and the US to model value chains outside of the European context or add more supplying countries.

This would require to update the .csv files in the folder "data" --> "transport" based on the approach described in the manuscript (...) (or any other approach). Further, the tab "Countries" in the file "Value_chains.xlsx" that is loaded with
```python

ppplca.install()
```
would need to be updated to include the updated list of possible countries.

3. Conduct LCAs for different products or update the process parameters for the available processes.

This would require different model parameters tailored to the products of interest. They can be set up as shown for pea, soy, and wheat proteins in the excel file "Processing_data.xlsx" that is loaded with
```python

ppplca.install()
```