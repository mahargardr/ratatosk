import pandas as pd
import re
from .exceptions import InvalidHeaderError 

class ConfigReference:
    def __init__(self,reference_file_path):
        self.filePath = reference_file_path
        self.settings = self.__load_reference()
        self.paramGroup = self.__create_param_group()
        self.moList = self.__get_mo_list()

    def __get_mo_list(self):
        df = self.settings.copy()
        df['sub_mo'] = df['MO'].str.split('=').str[0]
        df['mo_id'] = ''
        df.loc[df['MO'].str.contains('='), 'mo_id'] = df['MO'].str.split('=').str[1]

        # type_dict = df.set_index('sub_mo').to_dict()['Type']

        mo_s = list(pd.unique(df['MO']))

        mo_s.sort()
        mo_dict = {}

        for mo in mo_s:
            sub_mo = mo.split('=')[0]
            df_mo = df.loc[df['sub_mo']==sub_mo]
            mo_id = sub_mo.lower()+'id'
            if sub_mo not in mo_dict:

                if '=' in mo:
                    mo_ids = list(pd.unique(df_mo['mo_id']))
                else:
                    mo_ids = []

                parameters = list(pd.unique(df_mo['Parameter']))

                # type = type_dict[sub_mo]

                mo_dict[sub_mo] = {
                    mo_id : mo_ids,
                    'parameters' : parameters
                }
            else:
                continue

        dependencies = list(set(pd.unique(df['Dependency'])))
        for dependency in dependencies:
            mo_ids = ''
            mo_s = []
            if dependency != 'None':
                if '{' not in dependency:
                    mo_s=[dependency]
                else:
                    # Extract alphabets with dot before and after using regex
                    mo_s = re.findall(r'\b\w*\.\w*\b', dependency)

                for mo in mo_s:
                    sub_mo = mo.split('.')[0].split('=')[0]
                    param = mo.split('.')[1].lower()
                    if '=' in mo:
                        mo_ids = mo.split('.')[0].split('=')[1]
                    mo_id = sub_mo.lower()+'id'

                    if sub_mo not in mo_dict:
                        #print(sub_mo)
                        mo_dict[sub_mo] = {mo_id : [],
                                        'parameters' : []}
                        mo_dict[sub_mo]['parameters'] = [param]
                        if mo_ids != '':
                            mo_dict[sub_mo][mo_id] = [mo_ids]
                    else : 
                        if param not in mo_dict[sub_mo]['parameters']:
                            mo_dict[sub_mo]['parameters'].append(param)
                        if (mo_ids != '') and (mo_ids not in mo_dict[sub_mo][mo_id]):
                            mo_dict[sub_mo]['sub_id'].append(mo_ids)
        #print(mo_dict)
        return mo_dict
        
    def __load_reference(self):
        """
        This function load a reference configuration file, preprocess it and return the file as pandas dataframe if
        the header is valid and exit as invalid otherwise.
        """
        mandatory_columns = ['MO','Parameter']
        verified = False

        try:
            df_ref = pd.read_excel(self.filePath,index_col=None)
            print('Loading reference file')
        except FileNotFoundError:
            raise FileNotFoundError(f"Reference file not found at {self.filePath}")
        except ValueError:
            raise ValueError(f"Reference file {self.filePath} is not an excel file")
        
        ref_file_columns = list(df_ref.columns)

        for column in mandatory_columns:
            if column in ref_file_columns:
                verified = True
            else:
                verified = False
                break

        # if verified:
        #     types = list(pd.unique(df_ref['Type']))
        #     for type in types:
        #         type = type.lower()
        #         if (type!='regular') and (type!='relation'):
        #             raise ValueError(f"Invalid type value {type} in reference file {self.filePath}")

        if (not verified):
            raise InvalidHeaderError(f"Missing header in cell file {self.filePath}. Mandatory headers [MO, Parameter, Type] must be specified.")
        
        if "Parameter Indicator" not in df_ref:
            df_ref['Parameter Indicator'] = "Default Indicator"
        if "Group Parameter" not in df_ref:
            df_ref['Group Parameter'] = "Default Group"
        
        df_ref = df_ref.fillna('None')

        ### Expand the mo with format (qciprofilepredefined=qci1,qci2,qci3) ####
        
        def expand_mo(row):
            if '=' in row['MO']:
                parts = row['MO'].split('=')
                prefix = parts[0] + '='
                cars = parts[1].split(',')
                new_value = ','.join([prefix + car for car in cars])
                return pd.Series({'MO': new_value})
            else:
                return row[['MO']]

        # Apply the function to each row
        df_ref[['MO']] = df_ref.apply(expand_mo, axis=1)

        # Identify rows with multiple sub_id
        mask = df_ref['MO'].str.contains(',')

        # Split and expand rows with multiple sub_id
        expanded_rows = df_ref[mask].copy()
        expanded_rows['MO'] = expanded_rows['MO'].str.split(',')

        # Create a DataFrame with expanded rows
        expanded_df = expanded_rows.explode('MO')

        # Drop the original rows with multiple sub_id
        df_ref = pd.concat([df_ref[~mask],expanded_df], ignore_index=True)

        df_ref['Parameter'] = df_ref['Parameter'].str.replace(' ','').str.lower()
        df_ref['Dependency'] = df_ref['Dependency'].str.replace(' ','')
        df_ref['MO.Parameter'] = df_ref['MO']+'.'+df_ref['Parameter']

        #print(df_ref)

        return df_ref
        
    def __create_param_group(self):
        """
        This function create a list of dictionary relation of param indicator, group param, mo ,and parameter.
        """
        df = self.settings[['Parameter Indicator','Group Parameter','MO','Parameter']]

        indicator_dict = {}

        for indicator in pd.unique(df['Parameter Indicator']):
            df_indicator = df.loc[df['Parameter Indicator'] == indicator]

            indicator_dict[indicator] = {}

            for group in pd.unique(df_indicator['Group Parameter']):
                df_group = df_indicator.loc[df_indicator['Group Parameter'] == group]
                indicator_dict[indicator][group] = {}

                for mo in pd.unique(df_group['MO']):
                    df_mo = df_group.loc[df_group['MO'] == mo]
                    indicator_dict[indicator][group][mo] = list(pd.unique(df_mo['Parameter']))
                    
        return indicator_dict
