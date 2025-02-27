import pandas as pd
import os
import json
import zipfile
from typing import Optional

class cmPreProcessor():
    def __init__(
            self,
            cm_folder: str,
            s_date: str,
            sub_folders: Optional[list] = ['']
    ):
        self.cm_folder = cm_folder
        self.sub_folders = sub_folders
        self.date = s_date

    def run(
            self,
            define_site_type: bool = True,
            drop_featurestate_duplicate: bool = True,
            handle_sectorCarrier: bool = True,
            create_logicalchannelvalue: Optional[list] = [],
            handle_preproc: Optional[list] = [],
            file_type: str = 'csv'
    )-> None:
        '''
        Run preprocessing functions as specified in parameters.

        Paramters
        ---------
        define_site_type : bool, default True
            If ``True`` run method define_site_type()

        drop_featurestate_duplicate : bool, default True
            If ``True`` run method drop_featurestate_duplicate()
        
        handle_sectorCarrier : bool, default True
            If ``True`` run method handle_sectorCarrier()

        create_logicalchannelvalue : ['MO1','MO2'] list of mo to process, default empty list
            If not empty run method create_logicalchannelvalue() for all MO listed

        handle_preproc : ['MO1','MO2'] list of mo to process, default empty list
            If not empty run method handle_preproc() for all MO listed
        
        Returns
        -------
        None
            No object return from this function as this is just an
            interface to run the preprocessor functions
        '''
        for subfolder in self.sub_folders:
            file_path = self.cm_folder+'/'+subfolder+'/'+self.date
            
            log_file = file_path+'/preprocess.json'
            if not os.path.exists(log_file):
                initial_log = {'define_site_type' : 0,
                               'drop_featurestate_duplicate' : 0,
                               'handle_sectorCarrier' : 0,
                               'create_logicalchannelvalue' : [],
                               'handle_preproc' : []}
                
                with open(log_file,'w') as file:
                    json.dump(initial_log, file, indent=4)
                print(f'Initial preprocess log for {subfolder} created.')
            
            with open(log_file, 'r') as file:
                preprocess_log = json.load(file)
                print(f"Loading preprocess log {subfolder}.")
            
            try:
                if define_site_type and (preprocess_log['define_site_type'] == 0):
                    print(f"  Defining site type in {file_path}")
                    self.define_site_type(file_path,file_type)
                    preprocess_log['define_site_type'] = 1
            except Exception as e:
                print(e)
            
            try:    
                if drop_featurestate_duplicate and (preprocess_log['drop_featurestate_duplicate'] == 0):
                    print(f"  Dropping featureState duplicates in {file_path}")
                    self.drop_featurestate_duplicate(file_path,file_type)
                    preprocess_log['drop_featurestate_duplicate'] = 1
            except Exception as e:
                print(e)
                
            try:
                if handle_sectorCarrier and (preprocess_log['handle_sectorCarrier'] == 0):
                    print(f"  Modifying sectorCarrier in {file_path}")
                    self.handle_sectorCarrier(file_path,file_type)
                    preprocess_log['handle_sectorCarrier'] = 1
            except Exception as e:
                print(e)
            
            try:
                if len(create_logicalchannelvalue)>0:
                    print(f"  Creating logical channel in {file_path} for")
                    for mo in create_logicalchannelvalue:
                        print(f"   {mo}")
                        if mo not in preprocess_log['create_logicalchannelvalue']:
                            self.create_logicalchannelvalue(file_path,mo,file_type)
                            preprocess_log['create_logicalchannelvalue'].append(mo)
            except Exception as e:
                print(e)
            
            try:
                if len(handle_preproc)>0:
                    print(f"  Handling preprocess in {file_path}")
                    for mo in handle_preproc:
                        if mo not in preprocess_log['handle_preproc']:
                            self.handle_preproc(file_path,mo,file_type)
                            preprocess_log['handle_preproc'].append(mo)
            except Exception as e:
                print(e)
            
            with open(log_file, 'w') as file:
                json.dump(preprocess_log, file, indent=4)
                print("Preprocess log updated.")
             
            print("\n")

        return None

    def define_site_type(self,folder,file_type="csv"):
        '''
        This function define site type for MO EUtranCellFDD and EUtranCellTDD.
        Site types define as "I" for indoor and "M" for outdoor.
        'eutrancellfddid' and 'eutrancelltddid' is the cell identifier column.
        Cell defined as BKT402ML1. The 6th character is the site type.
        input : folder
        output : EUtranCellFDD and EUtranCellTDD MO CM file updated with site type
        '''
        df_fdd = pd.read_csv(folder+f'/EUtranCellFDD.{file_type}',index_col=None)
        df_tdd = pd.read_csv(folder+f'/EUtranCellTDD.{file_type}',index_col=None) 

        df_fdd['SiteType'] = df_fdd['eutrancellfddid'].str[6]
        df_tdd['SiteType'] = df_tdd['eutrancelltddid'].str[6]

        df_fdd.loc[df_fdd['SiteType']!='I','SiteType'] = 'M'
        df_tdd.loc[df_tdd['SiteType']!='I','SiteType'] = 'M'

        df_fdd.to_csv(folder+'/EUtranCellFDD.csv',index=None)
        df_tdd.to_csv(folder+'/EUtranCellTDD.csv',index=None)

        if file_type=='zip':
            self.__save_in_zip(folder+f'/EUtranCellFDD.{file_type}')
            self.__save_in_zip(folder+f'/EUtranCellTDD.{file_type}')
        
        print("   Done")

    def drop_featurestate_duplicate(self,folder,file_type="csv"):
        '''
        This function drop duplicates in featurestate MO defined by unique
        mecontext and featurestateid.
        input : folder
        output : Featurestate MO CM with unique mecontext and featurestateid.
        '''
        df = pd.read_csv(folder+f'/FeatureState.{file_type}',index_col=None)
        df = df.sort_values(by='featureState',ascending=False)
        df = df.drop_duplicates(subset=['mecontext','featurestateid'],keep='first')

        df.to_csv(folder+'/FeatureState.csv',index=None)

        if file_type=='zip':
            self.__save_in_zip(folder+f'/FeatureState.{file_type}')

        print("   Done")

    def handle_sectorCarrier(self,folder,file_type="csv"):
        sectorCarrier_file = '%s/SectorCarrier.%s' %(folder,file_type)
        eutrancelllFDD_file = '%s/EUtranCellFDD.%s' %(folder,file_type)
        eutrancelllTDD_file = '%s/EUtranCellTDD.%s' %(folder,file_type)

        df_sectorCarrier = pd.read_csv(sectorCarrier_file, delimiter=",", index_col=None, header='infer',low_memory=False, nrows=1)

        if ('eutrancellfddid' in df_sectorCarrier.columns) and ('eutrancelltddid' in df_sectorCarrier.columns):
            print('   Cell has been added to sectorCarrier')
        elif ('eutrancellfddid' not in df_sectorCarrier.columns) or ('eutrancelltddid' not in df_sectorCarrier.columns):
            print('Modifying %s' %sectorCarrier_file)
            df_fdd = pd.read_csv(eutrancelllFDD_file, delimiter=",", index_col=None, header='infer',low_memory=False)
            df_tdd = pd.read_csv(eutrancelllTDD_file, delimiter=",", index_col=None, header='infer',low_memory=False)
            df_sectorCarrier = pd.read_csv(sectorCarrier_file, delimiter=",", index_col=None, header='infer',low_memory=False)

            df_fdd = df_fdd[['mecontext', 'eutrancellfddid', 'sectorCarrierRef']]
            df_tdd = df_tdd[['mecontext', 'eutrancelltddid', 'sectorCarrierRef']]

            #df_fdd = df_fdd.rename(columns={'eutrancellfddid': 'eutrancellid'})
            #df_tdd = df_tdd.rename(columns={'eutrancelltddid': 'eutrancellid'})
            
            #df_cell = pd.concat([df_fdd,df_tdd], axis=0, ignore_index=True, sort=False)
            #df_cell['vsDataSectorCarrier'] = df_cell['sectorCarrierRef'].str.split('=').str[-1]
            #df_cell['mapping'] = df_cell['mecontext'].astype('str') + df_cell['vsDataSectorCarrier'].astype('str')
            
            df_fdd['vsDataSectorCarrier'] = df_fdd['sectorCarrierRef'].str.split('=').str[-1]
            df_fdd['mapping'] = df_fdd['mecontext'].astype('str') + df_fdd['vsDataSectorCarrier'].astype('str')
            
            df_tdd['vsDataSectorCarrier'] = df_tdd['sectorCarrierRef'].str.split('=').str[-1]
            df_tdd['mapping'] = df_tdd['mecontext'].astype('str') + df_tdd['vsDataSectorCarrier'].astype('str')

            #df_sectorCarrier = df_sectorCarrier[['mecontext', 'sectorcarrierid']]
            df_sectorCarrier['mapping'] = df_sectorCarrier['mecontext'].astype('str') + df_sectorCarrier['sectorcarrierid'].astype('str')

            dict_fdd = df_fdd.set_index('mapping').to_dict()['eutrancellfddid']
            dict_tdd = df_tdd.set_index('mapping').to_dict()['eutrancelltddid']
            
            df_sectorCarrier['eutrancellfddid'] = df_sectorCarrier['mapping'].map(dict_fdd)
            df_sectorCarrier['eutrancelltddid'] = df_sectorCarrier['mapping'].map(dict_tdd)

            df_sectorCarrier.to_csv(sectorCarrier_file.replace('.zip','.csv'), index=False)

            if file_type=='zip':
                self.__save_in_zip(sectorCarrier_file)

            print('   Done')

    def handle_preproc(self,folder, mo, file_type="csv"):
        file = f'{folder}/{mo}.{file_type}'

        df = pd.read_csv(file, delimiter=",", index_col=None, header='infer',low_memory=False, nrows=1)

        if 'modified' in df.columns:
            print('   %s has been modified' %mo)
        elif 'modified' not in df.columns:
            df = pd.read_csv(file, delimiter=",", index_col=None, header='infer',low_memory=False)
            if mo == 'QciProfilePredefined': 
                df['drxProfileRef'] = df['drxProfileRef'].str.split('=').str[-1]
                df['logicalChannelGroupRefValue'] = df['logicalChannelGroupRef'].str[-1]
                df['modified'] = 1
            elif mo == 'QciProfileOperatorDefined':
                df['drxProfileRef'] = df['drxProfileRef'].str.extract(r'DataDrxProfile=([^,\s]+)')
                df['logicalChannelGroupRefValue'] = df['logicalChannelGroupRef'].str[-1]
                df['modified'] = 1
            elif mo == 'ReportConfigSearch': 
                df['qcia1a2throffsets_qciprofilerefValue'] = df['qciA1A2ThrOffsets_qciProfileRef'].str.split('=').str[-1]
                df['modified'] = 1
            elif mo == 'SubscriberGroupProfile': 
                df['preschedProfileRef'] = df['preschedProfileRef'].str.split('=').str[-1]
                df['modified'] = 1
            elif mo == 'RlfProfile': 
                df['reservedBy_ori'] = df['reservedBy']
                df['reservedBy'] = df['reservedBy'].str.extract(r'QciProfilePredefined=([^,\s]+)')
                df['modified'] = 1

            df.to_csv(file.replace('.zip','.csv'), index=False)

            if file_type=='zip':
                self.__save_in_zip(file)
            
            print('   Done')

    def create_logicalchannelvalue(self,folder,mo, file_type="csv"):
        file = f'{folder}/{mo}.{file_type}'
        df = pd.read_csv(file,index_col=None)
    
        df['logicalChannelGroupRefValue'] = df['logicalChannelGroupRef'].str[-1]

        if len(df)>1:
            df.to_csv(file.replace('.zip','.csv'), index=False)

        if file_type=='zip':
            self.__save_in_zip(file)

        print('   Done')

    def merge_fdd_tdd(self,folder,file_type="csv"):
        '''
        This function EUtranCellFDD and EUtranCellTDD function into one
        CM file called EUtranCellFDD_TDD if one hasnt been created in a folder.
        input : folder
        output : EUtranCellFDD_TDD.csv file in the specified folder.
        '''
        print('Checking EUtranCellFDD_TDD...')
        if 'EUtranCellFDD_TDD.csv' not in os.listdir(folder) :
            print('     Merging EUtranCellFDD and TDD at %s'%folder)
            
            df_fdd = pd.read_csv(folder+'/EUtranCellFDD.csv',index_col=None)
            df_tdd = pd.read_csv(folder+'/EUtranCellTDD.csv',index_col=None)

            df_fdd = df_fdd.rename(columns={'eutrancellfddid':'eutrancellid'})
            df_tdd = df_tdd.rename(columns={'eutrancelltddid':'eutrancellid'})

            df_merge = pd.concat([df_fdd,df_tdd],ignore_index=True)

            df_merge.loc[pd.isnull(df_merge['dlChannelBandwidth']),'dlChannelBandwidth'] = df_merge['channelBandwidth']     
            #df_merge[['dlChannelBandwidth','channelBandwidth']]

            df_merge.loc[df_merge['eutrancellid'].str[7]=='L','dlChannelBandwidth'] = 17700

            df_merge.to_csv(folder+'/EUtranCellFDD_TDD.csv',index=None)
            print('     Done.')
        else:
            print('     EUtranCellFDD_TDD.csv exist at %s'%folder)
    
    def __save_in_zip(self,file):
        #hapus current zip
        os.remove(file)

        csv_file = file.replace('.zip','.csv')
        
        # Create a new zip file and add the modified CSV file to it
        with zipfile.ZipFile(file, 'w') as new_zip_file:
            new_zip_file.write(csv_file,os.path.basename(csv_file))


