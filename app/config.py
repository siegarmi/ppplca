import configparser

def load_config(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    
    # Convert it to a dictionary
    config_dict = {section: dict(config.items(section)) for section in config.sections()}
    
    return config_dict

def config(key):
    keys = key.split('.')  # Split the dot-separated string into a list of keys
    value = load_config('config/config.ini')
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return None 
    
    return value

