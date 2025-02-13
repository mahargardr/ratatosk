import pandas as pd
from collections import OrderedDict
from typing import Optional, Dict

class Cm:
    def __init__(self,mo,s_date,df):
        self.mo = mo
        self.date = s_date
        self.configuration = df

    def to_mo_format(self):
        cm = self.configuration.copy()
        df_formatted = pd.DataFrame(columns=['mecontext','MO Class','MO','Parameter','Value'])

        cm['MO'] = ''
        cm['MO Class'] = self.mo

        col_no = 0
        last_id_col_pos = -1
        first_id_found = False
        for col in cm.columns:
            if col.endswith('id'):
                first_id_found = True
                cm.loc[cm['MO']!='','MO'] = cm['MO']+','
                cm['MO'] = cm['MO']+'%s='%col.replace('id','')
                cm['MO'] = cm['MO']+cm[col].astype(str).str.replace('\.0','')
                last_id_col_pos = col_no
            else:
                if first_id_found :
                    last_id_col_pos = col_no
                    break
            col_no += 1
            
        parameters = list(cm.iloc[:, last_id_col_pos:].columns)
        cm['Parameter'] = ''
        for param in parameters:
            if (param != 'MO') and (param != 'MO Class') and (param not in df_formatted.columns):
                df_formatted_param = cm[['mecontext','MO Class','MO','Parameter',param]]
                df_formatted_param['Parameter'] = param
                df_formatted_param = df_formatted_param.rename(columns={param : 'Value'})
                df_formatted = pd.concat([df_formatted,
                                            df_formatted_param])
        
        return df_formatted

    def drop_featurestate_duplicate(self):
        '''
        This function drop duplicates in featurestate MO defined by unique
        mecontext and featurestateid.
        '''
        df_config = self.configuration.reset_index()
        df_config = df_config.sort_values(by='featureState',ascending=False)
        df_config = df_config.drop_duplicates(subset=['mecontext','featurestateid'],keep='first')

        return df_config

    def define_eutrancell_sitetype(self):
        '''
        This function define site type for MO EUtranCellFDD and EUtranCellTDD.
        Site types define as "I" for indoor and "M" for outdoor.
        'eutrancellfddid' and 'eutrancelltddid' is the cell identifier column.
        Cell defined as BKT402ML1. The 6th character is the site type.
        '''
        fdd_id = 'eutrancellfddid'
        tdd_id = 'eutrancelltddid'

        df_config = self.configuration.reset_index()

        if (fdd_id not in df_config.columns) and (tdd_id not in df_config.columns):
            raise TypeError("This cm is not eutrancellrelation type thus cannot be proceed.")
        if (fdd_id in df_config.columns):
            df_config['SiteType'] = df_config['eutrancellfddid'].str[6]
        if (tdd_id in df_config.columns):
            df_config['SiteType'] = df_config['eutrancelltddid'].str[6]

        df_config.loc[df_config['SiteType']!='I','SiteType'] = 'M'
        df_config.loc[df_config['SiteType']!='I','SiteType'] = 'M'

        return df_config

    def convert_column(
            self,
            columns: Dict[str,Dict[any,any]],
            keep_value: bool = True,
            keep_in_column: str ='preserved_column'
    ) -> pd.DataFrame :
        
        '''
        Translate any column value to prefered format.

        Parameters
        ----------
        columns : {'earfcn' : {'value1' : 'newvalue1'}}, required 
            Dictionary with column name as key and the conversion map as value.
            current value not specified in conversion map dictionary will be dropped. 

        keep_value : bool, default ``True`` 
            If ``True``, current existing value will be preserved in ``keep_in_column``.
            If ``False``, value in ``column`` will be overwritten

        keep_in_column : string, default ``preserved_column``
            Column name to preserve current existing value. Only take effect if keep_value=True.
            keep_in_column cannot be similar to column name.

        Returns
        -------
        DataFrame
            Return pandas dataframe with converted column value
        '''
        for col in columns:
            if (keep_in_column == col) and (keep_value):
                raise ValueError('Keep column cannot have same name with converted column unless keep value is set to False')
            col = col.lower()
            df = self.configuration.loc[self.configuration[col].isin(columns[col])]
            if keep_value:
                df[keep_in_column] = df[col]
            df[col] = df[col].map(columns[col])

        return df

    def filter_eutrancellrelation(
            self,
            enbid_lookup_dict,
            criteria='cosite'
    ):
        '''
        Filter eutrancellrelation-type cm which to only cosite/cosector target.
        enbid_lookup_dict : dictionary consisting of eNodeBId and nodeid mapping (enodebfunction mo)
        '''

        mo_id = self.mo.lower()+'id'
        
        if mo_id not in self.configuration.columns:
            raise TypeError("This cm is not eutrancellrelation type thus cannot be proceed.")
        
        df_config = self.configuration

        df_config['target_enbid'] = df_config[mo_id].str.split('-').str[1]

        df_config['source_enbid'] = df_config['mecontext'].map(enbid_lookup_dict)

        if criteria == 'cosite':
            df_config['cosite'] = 0
            df_config.loc[df_config['source_enbid'] == df_config['target_enbid'], 'cosite'] = 1

        else:
            '''
            Add cosector or other filtering rules here.
            '''
            pass
        df_config = df_config.loc[df_config[criteria]==1]
        return df_config
        
class cmCollector:
    '''
    Collector for cm of any MO. no attribute should be
    defined to initialized this object
    '''
    def __init__(self):
        pass

    def collect_cm(
            self,
            mo: str,
            s_date: str,
            cm_folder: str,
            parameters: Optional[list] = [],
            filters: Optional[Dict[str,list]] = {},
            sub_folders: Optional[list] = [],
            file_ext: str = 'csv'
    ) -> Cm :
        ''' 
        Return CM object of cm files from all folder/subfolders for a specific MO.

        Parameters
        ----------
        mo : MO configuration to be collected.
             make sure lower and uppercase match the cm file.
             e.g. "EUtranCellFDD", "FeatureState", "QciProfilePredefined"

        s_date : "YYYYMMDD" date of the cm to be collected.

        cm_folder : Main folder to search for the cm files

        parameters : ['param1','param2','param3',...], default empty.
                     list of param to collect from the MO.
                     If empty or not specified all param will be returned.
                     if param specified not exist in the MO, error will be raised.

        filters : {'col1' : ['value1'],'col2' : ['value2','value1']}, default empty.
                  dictionary of column label and value to use as filter for the CM
                  If empty,not specified,or filter not exist in cm, no filter will be applied.

        sub_folders : ['subfolder1', 'subfolder2', ...], the subfolders to look into if cm
                      stored in multiple folder like multiple ENM for example.
                      If not specified CM will be searched only in the ``cm_folder``.

        Returns
        -------
        Cm
            configuration file object
        '''

        print(f'Loading CM File : {mo}')

        if len(sub_folders)>0:
            df_config = pd.DataFrame()
            for sub_folder in sub_folders:
                cm_file = f'%s/%s/%s/%s.{file_ext}'%(cm_folder,sub_folder,s_date,mo)
                df = self.read_cm_file(cm_file=cm_file,
                                       parameters=parameters,
                                       filters=filters
                                       )
                df['folder'] = sub_folder
                if len(df_config )>0:
                    df_config = pd.concat([df_config,df],ignore_index=True)
                else:
                    df_config = df
        else:
            cm_file = f'%s/%s/%s.{file_ext}'%(cm_folder,s_date,mo)
            df_config = self.read_cm_file(cm_file=cm_file,
                                       parameters=parameters,
                                       filters=filters
                                       )
        
        if len(df_config)>0:
            print("  Done")
        else:
            print("  Empty")
        
        return Cm(mo,s_date,df_config)

    def read_cm_file(
            self,
            cm_file:str,
            parameters: Optional[list] = [],
            filters: Optional[Dict[str,list]] = {}
    ) -> pd.DataFrame :
        
        """
        Return Pandas dataframe of a specific cm file if valid and return empty dataframe otherwise.

        Parameters
        ----------
        cm_file : cm file path to be read

        parameters : ['param1','param2','param3',...], default empty.
                     list of param to collect from the MO.
                     If empty or not specified all param will be returned.
                     if param specified not exist in the MO, error will be raised.

        filters : {'col1' : ['value1'],'col2' : ['value2','value1']}, default empty.
                  dictionary of column label and value to use as filter for the CM
                  If empty,not specified,or filter not exist in cm, no filter will be applied.

        Returns
        -------
        DataFrame
            a pandas dataframe from the cm file
        """
        #print(filters)
        try:
            if (cm_file.endswith('.csv') or cm_file.endswith('.zip')):
                df_config = pd.read_csv(cm_file,index_col=None)
            elif cm_file.endswith('.xlsx'):
                df_config = pd.read_excel(cm_file,index_col=None)

            if len(df_config)==0:
                raise FileNotFoundError(f"No valid file found. Please check the folder path and/or the sub_folders.")

            df_config['siteid'] = df_config['mecontext'].str.extract(r"([A-Za-z]{3}\d{3})")

            columns = ['mecontext','siteid']

            if 'eutrancellfddid' in df_config.columns:
                columns.append('eutrancellfddid')
            if 'eutrancelltddid' in df_config.columns:
                columns.append('eutrancelltddid')
            if 'nrcellduid' in df_config.columns:
                columns.append('nrcellduid')
                
            #print(f"df size : {len(df_config)}")
            ### Filtering ###
            if len(filters)>0:
                #print(filters)
                if ('eutrancellfddid' in columns) or ('eutrancelltddid' in columns) or ('nrcellduid' in columns):
                    split_dfs = []
                    if 'eutrancellfddid' in columns:
                        df_config_fdd = df_config[df_config['eutrancellfddid'].notna()]
                        df_config_fdd = self.filter_cm(df_config_fdd.drop(columns=['eutrancelltddid','nrcellduid'],errors='ignore'),filters)
                        split_dfs.append(df_config_fdd)
                    if 'eutrancelltddid' in columns:
                        df_config_tdd = df_config[df_config['eutrancelltddid'].notna()]
                        df_config_tdd = self.filter_cm(df_config_tdd.drop(columns=['eutrancellfddid','nrcellduid'],errors='ignore'),filters)
                        split_dfs.append(df_config_tdd)
                    if 'nrcellduid' in columns:
                        df_nr = df_config[df_config['nrcellduid'].notna()]
                        df_nr = self.filter_cm(df_nr.drop(columns=['eutrancellfddid','eutrancelltddid'],errors='ignore'),filters)
                        split_dfs.append(df_nr)
                    
                    if len(split_dfs)>1:
                        df_config = pd.concat(split_dfs, ignore_index=True)
                    elif len(split_dfs)==1:
                        df_config = split_dfs[0]

                else:
                    df_config = self.filter_cm(df_config,filters)
            
                for filter in filters:
                    if (filter in df_config.columns) and (filter not in columns):
                        columns.append(filter)

            ## Return all ID columns and parameters column ###
            for col in df_config.columns:
                if (col not in columns) & (col != 'unknown_id'):
                    if col.endswith('id'):
                        columns.append(col)
                    else:
                        if len(parameters) == 0:
                            columns.append(col.lower())

            df_config.columns = df_config.columns.str.lower()
            if len(parameters)>0:
                for param in parameters:
                    if param in df_config.columns:
                        columns.append(param)

            df_config = df_config[list(OrderedDict.fromkeys(columns))]
            #print(f"df size after filter: {len(df_config)}")
        
        except Exception as err:
            print(f"Failed to read cm_file {cm_file} with error {err}")
            df_config = pd.DataFrame()

        return df_config
    
    def filter_cm(self,df,filters={}):
        #print(f"filters : {filters}")
        for filter in filters:
            if filter in df.columns:
                if (filter != 'eutrancellfddid') and (filter != 'eutrancelltddid') and (filter != 'nrcellduid'):
                    df[filter] = df[filter].astype(str).str.replace('\.0','')
                df = df.loc[df[filter].isin(filters[filter])]
        return df