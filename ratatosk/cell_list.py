import pandas as pd
from datetime import datetime, timedelta
from dateutil import rrule
import os

from ratatosk.global_config import GlobalConfig
from .exceptions import InvalidHeaderError 

class CellList:
    def __init__(self,cells_file_path,filter_by):
        self.cells_file_path = cells_file_path
        self.cells = self.load_cells(filter_by)
        
    def load_cells(self,filter_by):
        """
        This function load a cells file, read it and return the file as pandas dataframe if
        the header is valid and return empty dataframe otherwise.
        """
        
        filter_columns_map = {'node':'mecontext',
                             'cell':'cell',
                             'site':'siteid',
                             'ne' : 'ne'}
        
        if isinstance(filter_by, str) :
            filter_column = filter_columns_map[filter_by]
        else:
            filter_column = 'enm'

        try:
            if self.cells_file_path != 'all':
               df_cells = pd.read_excel(self.cells_file_path,index_col=None)
               if filter_column not in df_cells.columns:
                  raise InvalidHeaderError(f"Missing header in cell file {self.cells_file_path}. Mandatory {filter_column} header for filter by {filter_by}.")
        except FileNotFoundError:
            raise FileNotFoundError(f"Cells file not found at {self.cells_file_path}")
        except ValueError:
            raise ValueError(f"Cells file {self.cells_file_path} is not an excel file")

        #Check if all cell list available
        s_date = datetime.now().strftime("%Y%m%d")
        all_cell_file = f"/var/opt/pmt/data/all_cell_list/all_cell_list_{s_date}.csv"
            
        if all_cell_file.split("/")[-1] not in os.listdir("/var/opt/pmt/data/all_cell_list"):
           #print(all_cell_file)
           #print(os.listdir("/var/opt/pmt/data/all_cell_list"))
           self.get_cell_list()
            
        #print(df_cells)
        df_all_cell = pd.read_csv(all_cell_file)
        df_all_cell['ne'] = df_all_cell['cell'].str.extract(r"([A-Za-z]{3}\d{3}[A-Za-z]{2})")
        
        if filter_column == 'enm':
           df_all_cell = df_all_cell.loc[df_all_cell[filter_column].isin(filter_by)]
        elif self.cells_file_path != 'all':    
           df_all_cell = df_all_cell.loc[df_all_cell[filter_column].isin(df_cells[filter_column])]
        #print(df_all_cell)
            
        return df_all_cell

    def get_cell_list(self):
        global_config_path = os.path.join(os.path.dirname(__file__), 'config.json')
        global_config    = GlobalConfig(global_config_path)
        
        cm_folder = global_config.get_parameter('cm_folder')
        enm = ["enm7","enm8","enm9","enm11"]
    
        fdd_columns = ['mecontext', 'eutrancellfddid', 'dlChannelBandwidth']
        tdd_columns = ['mecontext', 'eutrancelltddid', 'channelBandwidth']
        print("getting all cell list")
    
        df_result = pd.DataFrame()
        for dt in rrule.rrule(rrule.DAILY, dtstart=(datetime.now()-timedelta(days=7)), until=datetime.now()):
            s_date = dt.strftime("%Y%m%d")
            #print(s_date)
    
            i = 0
            for enm_list in enm:
                if (enm_list == 'filtered'):
                   continue
                #print('Getting ENM: %s' %enm_list)
                folder = cm_folder + '/' + enm_list + '/' + s_date
                eutrancelllFDD_file = '%s/EUtranCellFDD.csv' %(folder)
                eutrancelllTDD_file = '%s/EUtranCellTDD.csv' %(folder)
                try:
                    try:
                       #print('read csv')
                       df_fdd = pd.read_csv(eutrancelllFDD_file, delimiter=",", index_col=None, header='infer',low_memory=False, usecols=fdd_columns)
                       df_tdd = pd.read_csv(eutrancelllTDD_file, delimiter=",", index_col=None, header='infer',low_memory=False, usecols=tdd_columns)
        
                    except:
                       #print('read zip')
                       df_fdd = pd.read_csv(eutrancelllFDD_file+'.zip', delimiter=",", index_col=None, header='infer',low_memory=False, usecols=fdd_columns)
                       df_tdd = pd.read_csv(eutrancelllTDD_file+'.zip', delimiter=",", index_col=None, header='infer',low_memory=False, usecols=tdd_columns)
                    
                    df_fdd = df_fdd.rename(columns={'eutrancellfddid':'cell'})
                    df_tdd = df_tdd.rename(columns={'eutrancelltddid':'cell'})
                    df_tdd = df_tdd.rename(columns={'channelBandwidth':'dlChannelBandwidth'})
    
                    df_cell = pd.concat([df_fdd,df_tdd], axis=0, ignore_index=True, sort=False)
                    df_cell['enm'] = enm_list
    
                    if i == 0:
                        df_eutrancell = df_cell
                        i = 1
                    elif i == 1:
                        df_eutrancell = pd.concat([df_eutrancell,df_cell], axis=0, ignore_index=True, sort=False)
                except Exception as err:
                    pass
                    print(err)
                
                #print('     number fdd: %s' %len(df_fdd))
                #print('     number tdd: %s' %len(df_tdd))
    
            try:
               #print('Getting all ENM within a week')
               df_eutrancell['date'] = s_date
               if len(df_result) > 0:
                   df_result = pd.concat([df_result,df_eutrancell], axis=0, ignore_index=True, sort=False)
                   #print('     number file in %s: %s' %(s_date,len(df_fdd)))
               elif len(df_result) == 0:
                   df_result = df_eutrancell
                   #print('     number file in %s: %s' %(s_date,len(df_fdd)))
            except:
               pass
        
        #print('number final: %s' %len(df_result))
        df_result['siteid'] = df_result['cell'].str.extract(r'([A-Za-z]{3}\d{3})')
    
        df_result.dropna()
        df_result  = df_result.drop_duplicates(subset=['cell'])
    
        df_result.to_csv("/var/opt/pmt/data/all_cell_list/all_cell_list_%s.csv" %s_date, index=False)
        