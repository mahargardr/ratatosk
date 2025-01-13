import json

global_config_file = "config.json"

class GlobalConfig:
    def __init__(self,config_file_path):
        self.config_file_path = config_file_path
        self.config_data = self.load_config()
        
    def load_config(self):
        """
        Load config.json to load predefined variables for the whole program
        """
        try:
            with open(self.config_file_path,'r') as config_file:
                config_data = json.load(config_file)
            return config_data
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found at {self.config_file_path}")
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format in the configuration file")
        
    def get_parameter(self,parameter_name):
        return self.config_data.get(parameter_name)
    

def loadGlobalConfig():
    return GlobalConfig(global_config_file)