class ValueChain:
    def __init__(self, product, location_string):
        crop_name, crop_name_short = ValueChain.get_crop_name(product)

        self.product = product
        self.crop_name = crop_name  
        self.crop_name_short = crop_name_short
        self.location_string = location_string
        self.production_stages = {}
    
    def addStage(self, stage_name, stage):
        self.production_stages[stage_name] = stage
    
    def getStage(self, stage_name):
        return self.production_stages[stage_name]
    
    @staticmethod
    def get_crop_name(product):
        if product == "SPI" or product == "SPC":
            crop_name = "Soybeans"
            crop_name_short = "Soy"
        elif product == "PPI" or product == "PPC":
            crop_name = "Peas"
            crop_name_short = "Pea"
        elif product == "gluten":
            crop_name = "Wheat"
            crop_name_short = "Wheat"
        else:
            raise SystemExit("Code currently not set up for provided product. Please update function get_crop_name to include the product. Stopping execution.")
        return crop_name, crop_name_short