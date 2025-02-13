import pandas as pd
from datetime import datetime
import os
import re

from ratatosk.global_config import GlobalConfig
from ratatosk.cell_list import CellList
from ratatosk.config_reference import ConfigReference
from ratatosk.cm import cmCollector
from ratatosk.pre_processor import cmPreProcessor
from ratatosk.auditor import Auditor

def cmedit_query_function(
    object_list='',
    filter_by='node',
    reference='',
):
    if reference == '':
        print("generating cmedit query")
        raise ValueError("Please specify mo and param in reference file")
    
    node_str = '*'
    
    if object_list != '':
        node_list = CellList(object_list,filter_by).cells['mecontext'].unique()
        node_str =';'.join(node_list)
    
    config_reference = ConfigReference(reference)
    mo_dict = config_reference.moList
    
    mo_params = []
    for mo in mo_dict:
        params = mo_dict[mo]['parameters']
        
        if len(params)>1:
            param_str = ','.join(params)
            param_str = '('+param_str+')'
        elif len(params) == 1:
            param_str = params[0]
        else:
            continue
            
        mo_str = mo+'.'+param_str
        mo_params.append(mo_str)
        mo_param_str = ';'.join(mo_params)
        
        mo_param_str = re.sub(r'(\w+)_(\w+)',r'\1.{\2}', mo_param_str)
    
    cmedit_str = f'cmedit get {node_str} {mo_param_str} -t'
    with open('cmedit.txt','w') as file:
        file.write(cmedit_str)
    #print(cmedit_str)
        
    #print(node_str)
    #print(config_reference.moList['SectorCarrier'])
    
    return None

def get_cm_function( 
        mo, 
        date='', 
        parameters=[],
        filters={}, 
        cm_folder_path='',
        cm_subfolders='',
        file_ext='csv',
        output_folder_path='',
        format='cm-bulk'
):
    global_config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    global_config    = GlobalConfig(global_config_path)

    cmc = cmCollector()

    if cm_folder_path == '':
        cm_folder_path = global_config.get_parameter('cm_folder')
    if output_folder_path == '':
        output_folder_path = f'./{mo}_{format}_{date}.xlsx'
    if cm_subfolders == '':
        cm_subfolders = global_config.get_parameter('enm_list')

    if date == '':
        date = datetime.now().date().strftime("%Y%m%d")
    
    print(f"\nDate:{date}")
    print(f"CM Folder:{cm_folder_path}")
    print(f"Subfolders:{cm_subfolders}\n")

    cm = cmc.collect_cm(
        mo,
        date,
        cm_folder_path,
        parameters,
        filters,
        cm_subfolders,
        file_ext=file_ext
    )

    if format == 'cm-bulk':
        df = cm.configuration
    elif format == 'cm-list':
        df = cm.to_mo_format()
        if len(df)>1000000:
            print("Data row is too much for this format. Result will be capped to 999999 rows. Consider filtering or use cm-bulk format.")
            df = df.head(999999)
    
    print("Exporting.")
    if output_folder_path.endswith('csv'):
        df.to_csv(output_folder_path)
        print('  Done')
    elif output_folder_path.endswith('xlsx'):
        df.to_excel(output_folder_path)
        print('  Done')
    else:
        print(f"Failed to export to {output_folder_path} unrecognized format.")
    
    return None
    


def audit_cm_function( 
        cell_list_path, 
        reference_file_path, 
        global_config_path='',
        date='', 
        filter_by='node',
        cm_folder_path='',
        cm_subfolders='',
        file_ext='csv',
        output_folder_path='',
        verbose=False,
        preprocess=True
    ):
    '''
    
    '''

    ####################### Read Variables #############################

    if global_config_path=='':
        global_config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    global_config    = GlobalConfig(global_config_path)

    if cm_folder_path == '':
        cm_folder_path = global_config.get_parameter('cm_folder')
    if output_folder_path == '':
        output_folder_path = global_config.get_parameter('output_folder').replace(".xlsx",f"_{date}.xlsx")
    if cm_subfolders == '':
        cm_subfolders = global_config.get_parameter('enm_list')
    
    if date == '':
        date = datetime.now().date().strftime("%Y%m%d")
        
    if cell_list_path == 'all':
        cells = CellList(cell_list_path,cm_subfolders).cells
    else:
        cells = CellList(cell_list_path,filter_by).cells

    config_reference = ConfigReference(reference_file_path)
    print(f'\nEvaluated Cells : {len(pd.unique(cells.cell))}')
    print(f'Evaluated Nodes : {len(pd.unique(cells.mecontext))}\n')
    #print(config_reference.settings)
    
    print(f'Analyzing ENMs: {cm_subfolders}')
    print(f'Analyzing configuration date {date}\n')
    ####################################################################

    
    ############################ Preprocessing ##########################
    if preprocess :
        preprocessor = cmPreProcessor(
            cm_folder=cm_folder_path,
            sub_folders=cm_subfolders,
            s_date=date
        )
        print("Preprocessing")
        preprocessor.run(
            define_site_type=True,
            drop_featurestate_duplicate=True,
            handle_sectorCarrier=True,
            create_logicalchannelvalue=[
                'QciProfilePredefined',
                'QciProfileOperatorDefined'
            ],
            handle_preproc=[
                'QciProfilePredefined',
                'SubscriberGroupProfile',
                'QciProfileOperatorDefined',
                'ReportConfigSearch'
            ],
            file_type=file_ext
        )

    ######################################################################


    ############################## Load CM ###############################
    
    dict_df = {}
    cmc = cmCollector()

    for mo in config_reference.moList:
        parameters = config_reference.moList[mo]['parameters']
        
        if mo == 'FeatureState':
            parameters.append('description')
            
        filters = {}
        if filter_by == 'node':
            print("filter by node")
            filters['mecontext'] = list(cells['mecontext'])
        elif filter_by == 'site':
            print("filter by site")
            filters['siteid'] = list(cells['siteid'])
        elif (filter_by == 'cell') or (filter_by == 'ne'):
            print("filter by cell")
            filters['eutrancellfddid'] = list(cells['cell'])
            filters['eutrancelltddid'] = list(cells['cell'])
            filters['nrcellduid'] = list(cells['cell'])
        else:
            raise ValueError("Invalid Filter Option. Can only filter by 'node', 'site' or 'cell' ")

        mo_id = mo.lower()+'id'
    
        if len(config_reference.moList[mo][mo_id]) > 0:
            filters[mo_id] = config_reference.moList[mo][mo_id]
        #print(parameters)
        #print(filters.keys())
        cm = cmc.collect_cm(
                mo,
                date,
                cm_folder_path,
                parameters,
                filters,
                cm_subfolders,
                file_ext
            )
        
        #print(cm.configuration)

        #------- drop duplicates ------- #
        identifier_cols = ['mecontext','siteid','eutrancellfddid','eutrancelltddid','nrcellduid',mo_id]
        duplicate_col = []
        for col in cm.configuration.columns:
            if col in identifier_cols:
                duplicate_col.append(col)
        
        # if (mo_id in cm.configuration.columns) and (mo_id not in duplicate_col):
        #     duplicate_col.append(mo_id)

        if len(cm.configuration)>0:
            cm.configuration = cm.configuration.sort_values(by=duplicate_col,ascending=False)
            cm.configuration = cm.configuration.drop_duplicates(subset=duplicate_col,keep='first')

        #-------------------------------#

        #------- translate earfcn to band for freqrelation MO ------#
        #if 'freqrelation' in mo.lower():
        #    cm.configuration[mo_id] = cm.configuration[mo_id].astype(str)
        #    cm.configuration = cm.convert_column(
        #        columns={
        #            mo_id : global_config.get_parameter('earfcn_map'), 
        #        },
        #        keep_in_column='target_earfcn'
        #    )
        #----------------------------------------------------------#

        #-------- Select co-site only for cell relation MO ---------#
        if 'cellrelation' in mo.lower():
            ## load enodebfunction
            df_enbfunction = cmc.collect_cm(
                                'ENodeBFunction',
                                date,
                                cm_folder_path,
                                parameters=['enbid'],
                                filters={},
                                sub_folders=cm_subfolders,
                                file_ext=file_ext
                            ).configuration
            df_enbfunction['enbid'] = df_enbfunction['enbid'].astype(str).str.replace(".0","")
            dict_enb = df_enbfunction.set_index('mecontext').to_dict()['enbid']
            cm.configuration = cm.filter_eutrancellrelation(dict_enb)
            cm.configuration.to_csv("eutrancellrelation_debug.csv")
        #----------------------------------------------------------#

        #print(len(cm.configuration))
        #print(cm.configuration)
        dict_df[mo] = cm

    print("\n")
    #####################################################################
    

    ############################## Concheck #############################
    cm_auditor = Auditor()
    audit_result = cm_auditor.audit(
        config_reference,
        dict_df
    )
    print("\n")
    #print(audit_result.audit_result.keys())
    #####################################################################


    ############################# Formatting ############################
    audit_result.create_report(output_folder_path,
                               cells,
                               dict_df,
                               verbose)
    print(pd.read_excel(output_folder_path))