# ranterstellar/cli.py

import click
import json
import warnings
from ratatosk.main import audit_cm_function, get_cm_function,cmedit_query_function


@click.group()
def main():
    pass

@main.command()
@click.option('--object-list', default='', type=str, help='Cell or site list you want to use as filter')
@click.option('--reference', default='',type=str, help='Config reference to use as a checking guide')
@click.option('--config', default='',type=str, help='Global configuration file')
@click.option('--date', default='',type=str, help='CM date you want to evaluate')
@click.option('--filter-by', default='node',type=str, help='Types of filter you want to use; node, site or cell')
@click.option('--cm-folder', default='',type=str, help='Folder to look for CM files')
@click.option('--cm-subfolder', default='',type=str, help='Sub-folders to look for CM files in cm-folder')
@click.option('--verbose', default=False,type=bool, help='Choose generate simple summary or verbose report')
@click.option('--output', default='',type=str, help='Output folder path')
@click.option('--preprocess', default=True,type=bool, help='Run preprocess or not')
@click.option('--file-ext', default='csv',type=str, help='File Extension')
@click.option('--rat', default='',type=str, help='Radio access technology to be audit')
@click.option('--arg-file', default='',type=str, help='Path for command argument file')

def audit_cm(
    object_list,
    reference,
    config,
    date,
    filter_by,
    cm_folder,
    cm_subfolder,
    file_ext,
    output,
    verbose,
    preprocess,
    rat,
    arg_file,
):
    """
    Audit CM files based on reference. Can be filtered to audit only cell or site in objectList.
    """
    warnings.simplefilter("ignore")
    
    if arg_file != '':
       print("Running concheck with argument file")
       with open(arg_file, 'r') as file:
          args = json.load(file)
          
       object_list = args.get('object_list',object_list)
       reference = args.get('reference',object_list)
       config = args.get('config',object_list)
       date = args.get('date',object_list)
       filter_by = args.get('filter_by',object_list)
       cm_folder = args.get('cm_folder',object_list)
       cm_subfolder = args.get('cm_subfolder',object_list)
       verbose = args.get('verbose',object_list)
       output = args.get('output',object_list)
       preprocess = args.get('preprocess',object_list)
       rat = args.get('rat',object_list)
       file_ext = args.get('file_ext',object_list)
    
    
    if (object_list == '') :
        object_list = "all"
        print("Checking for all footprint cells") 
        #raise RuntimeError("Missing object list please specify with flag --object-list or in the argument file")
    elif (reference == ''):
        raise RuntimeError("Missing reference file please specify with flag --reference or in the argument file")
 
    audit_cm_function(
       object_list,
       reference,
       config,
       date,
       filter_by,
       cm_folder,
       cm_subfolder,
       file_ext,
       output,
       verbose,
       preprocess,
       rat
    )
    
@main.command()
@click.option('--object-list', default='', type=str, help='Cell or site list you want to use as filter')
@click.option('--filter-by', default='site',type=str, help='Types of filter you want to use; node, site or cell')
@click.option('--reference', default='',type=str, help='Config reference file with mo, param and dependency to extract from cmedit')

def cmedit_query(
    object_list,
    filter_by,
    reference,
):
    """
    Generate cmedit query 
    """
    warnings.simplefilter("ignore")
 
    cmedit_query_function(
        object_list,
        filter_by,
        reference,
    )
 
 
@main.command()
@click.option('--mo', required=True, type=str, help='MO to be collected. Case must match with CM files name.')
@click.option('--date', required=True,type=str, help='Date of CM files to be collected')
@click.option('--parameters', default="",type=str, help='(Optional) Selected parameters in format of list ["a","b"]')
@click.option('--filters', default="",type=str, help='(Optional) additional filters for the CM files with dictionary format {"key":["value1","value2"]}')
@click.option('--format', default='cm-bulk',type=str, help='(Optional) ["cm-bulk", "cm-list"], CM files format. Default=cm-bulk')
@click.option('--cm-folder', default='',type=str, help='Folder to look for CM files')
@click.option('--cm-subfolders', default='',type=str, help='Sub-folders to look for CM files in cm-folder')
@click.option('--output', default='',type=str, help='Output file path')
@click.option('--file-ext', default='csv',type=str, help='File Extension')

def get_cm(
    mo,
    date='',
    parameters="",
    filters="",
    format='cm-bulk',
    cm_folder='',
    cm_subfolders='',
    file_ext='csv',
    output='',
):
    """
    Get CM file for certain MO of a certain date configuration.
    """

    if parameters!="":
        parameters = parameters.split(",")
    if filters != "":
        try:
            print(filters)
            filters = json.loads(filters)
            print(type(filters))
        except json.JSONDecodeError as e:
            print(f"Error --filter format: {e}")

    warnings.simplefilter("ignore")
    get_cm_function( 
        mo, 
        date, 
        parameters,
        filters, 
        cm_folder,
        cm_subfolders,
        file_ext,
        output,
        format
    )

if __name__ == '__main__':
    main()