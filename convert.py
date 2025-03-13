import jinja2 as j2
import json
import numpy as np
import os
import pandas as pd
import re
import shutil
import sys
import utils.helpers as helpers
import xlsxwriter
import xml.dom.minidom
import xml.etree.ElementTree as ET

from io import BytesIO
from jinja2 import Environment, FileSystemLoader
from openpyxl.utils import get_column_letter

# Function to handle format extraction
def handle_format(element, format_type):
    element['input_extension'] = helpers.FORMATS[format_type]
    element['output_file_path'] = helpers.generate_output_file_path(element)
    
    match format_type:
        case 'xlsx':
            extract_components_to_xlsx(element)
        case 'json':
            extract_components_to_json(element)
        case 'xml':
            extract_components_to_xml(element)
        case 'html':
            extract_components_to_html(element)

def extract_components_to_xlsx(element):
    '''
    This function extracts components from an spreadsheet file and writes them to an spreadsheet file
    based on the components defined in the element dictionary
    It locks specific cells in each sheet and applies dropdown lists where necessary.

    Parameters:
    element (dict): A dictionary containing the following:
        - data_df (DataFrame): Data from the 'data' worksheet.
        - allowed_values_dict (dict): Mapping of allowed values for dropdowns.
        - output_file_path (str): The path to the output spreadsheet file.
        - standard_name (str): Namespace name (e.g. 'dwc', 'mixs', 'tol').
        - standard_label (str): Namespace label (e.g. 'Darwin Core', 'MIxS', 'ToL').
        - version_column_name (str): The name of the version column in the data_df.
        - technology_name (str): Technology name (e.g. 'single_cell', 'metagenomics', 'genomics').
        - technology_label (str): Technology label (e.g. 'Single Cell', 'Metagenomics', 'Genomics').
        - version_description (str): Description of the version column.
    '''
    data_df = element['data_df']
    allowed_values_dict = element['allowed_values_dict']
    output_file_path = element['output_file_path']
    standard_name = element['standard_name']
    standard_label = element['standard_label']
    version_column_name = element['version_column_name']
    technology_name = element['technology_name']
    technology_label = element['technology_label']
    version_description = element['version_description']

    bytesIO = BytesIO()

    with pd.ExcelWriter(bytesIO, engine='xlsxwriter', mode='w') as writer:
        workbook = writer.book  # Get the xlsxwriter workbook object

        # Cell formats
        locked_format = workbook.add_format({'locked': True})
        unlocked_format = workbook.add_format({'locked': False})

        desc_eg_format = workbook.add_format({
            'locked': True, 
            'text_wrap': True, 
            'italic': True,
            'font_color': '#808080'
        })

        merge_format = workbook.add_format({
            'bold': True,
            'align': 'left',
            'valign': 'vcenter',
            'bg_color': '#D3D3D3'
        })

        required_format = workbook.add_format({'bold': True, 'locked': True})

        # Create README worksheet
        readme_sheet_data = dict()
        readme_sheet_data['technology_name'] = technology_name
        readme_sheet_data['technology_label'] = technology_label
        readme_sheet_data['version_description'] = version_description
        readme_sheet_data['standard_name'] = standard_name
        readme_sheet_data['standard_label'] = standard_label
        readme_sheet_data['version_column_name'] = version_column_name
        readme_sheet_data['writer'] = writer
        readme_sheet_data['locked_format'] = locked_format

        helpers.create_readme_worksheet(readme_sheet_data)

        # Iterate through unique components
        for component_name in data_df['component_name'].unique():
            component_df = data_df[data_df['component_name'] == component_name].copy()

            # Get the name of the terms as the column names from the component DataFrame
            column_names = component_df['term_name'].tolist()

            # If there are no fields for this component, skip it
            if not column_names:
                continue

            # Prepare DataFrame for writing to spreadsheet
            df = pd.DataFrame(columns=column_names)

            # Extract metadata for formatting and validation
            required_columns = helpers.get_required_columns(component_df, version_column_name)
            col_desc_eg = helpers.get_col_desc_eg(component_df, version_column_name)

            # Remove NaNs columns (if any rows are present)
            if not df.empty:
                df.dropna(axis=1, how='all', inplace=True)

            # Write the DataFrame to an spreadsheet sheet
            sheet_name = helpers.get_worksheet_info(component_df)
            df.to_excel(writer, sheet_name=sheet_name, index=False, header=True)
            worksheet = writer.sheets[sheet_name]

            # Apply formatting and protection to the worksheet
            element = dict(
                worksheet=worksheet, 
                column_names=column_names,
                required_columns=required_columns,
                col_desc_eg=col_desc_eg,
                locked_format=locked_format,
                unlocked_format=unlocked_format,
                merge_format=merge_format,
                required_format=required_format,
                desc_eg_format=desc_eg_format
            )

            helpers.format_and_protect_worksheet(element)

            # Apply data validation
            helpers.apply_data_validation(component_df, df, writer, standard_name, allowed_values_dict)

        # Apply autofit to all sheets
        helpers.autofit_all_sheets(writer)

    # Save to output file
    directory_path = os.path.dirname(output_file_path) # Get the directory path
    os.makedirs(directory_path, exist_ok=True) # Create output directory if it does not exist
    file_name = os.path.basename(output_file_path)

    with open(output_file_path, 'wb') as f:
        f.write(bytesIO.getvalue())
    
    print(f"'{file_name}' created!")

def extract_components_to_json(element):
    json_data = helpers.get_base_schema_json(element)
    
    # Write JSON data to a file
    helpers.generate_json_file(json_data,  element['output_file_path'])

def extract_components_to_xml(element):
    '''
    This function extracts components from an spreadsheet file and writes them to an spreadsheet file
    based on the components defined in the element dictionary
    It locks specific cells in each sheet and applies dropdown lists where necessary.

    Parameters:
    element (dict): A dictionary containing the following:
        - data_df (DataFrame): Data from the 'data' worksheet.
        - allowed_values_dict (dict): Mapping of allowed values for dropdowns.
        - output_file_path (str): The path to the output spreadsheet file.
        - standard_name (str): Namespace prefix (e.g. 'dwc', 'mixs', 'tol').
        - version_column_name (str): The name of the version column in the data_df.
        - technology_name (str): Technology name (e.g. 'single_cell', 'metagenomics', 'genomics').
        - technology_label (str): Technology label (e.g. 'Single Cell', 'Metagenomics', 'Genomics').
        - version_description (str): Description of the version column.
    '''
    # Extract parameters
    data_df = element['data_df']
    allowed_values_dict = element['allowed_values_dict']
    output_file_path = element['output_file_path']
    standard_name = element['standard_name']
    version_column_name = element['version_column_name']

    # Ensure the output directory exists
    directory_path = os.path.dirname(output_file_path) # Get the directory path
    os.makedirs(directory_path, exist_ok=True) # Create output directory if it does not exist
    file_name = os.path.basename(output_file_path)

    # Extract checklist type details
    accession = f"{element['technology_name'].upper().replace('_','')}1"
    checklist_type = 'single_cell'
    checklist_label = element['technology_label']
    checklist_name = element['technology_name']
    checklist_description = element['version_description']

    # Create root element
    checklist_set = ET.Element('CHECKLIST_SET')

    # Create checklist element
    checklist = ET.SubElement(checklist_set, 'CHECKLIST', accession=accession, checklistType=checklist_type)

    # Create IDENTIFIERS
    identifiers = ET.SubElement(checklist, 'IDENTIFIERS')
    primary_id = ET.SubElement(identifiers, 'PRIMARY_ID')
    primary_id.text = accession

    # Create DESCRIPTOR
    descriptor = ET.SubElement(checklist, 'DESCRIPTOR')

    # Add static elements to descriptor
    label = ET.SubElement(descriptor, 'LABEL')
    label.text = checklist_label

    name = ET.SubElement(descriptor, 'NAME')
    name.text = checklist_name

    description = ET.SubElement(descriptor, 'DESCRIPTION')
    description.text = checklist_description

    authority = ET.SubElement(descriptor, 'AUTHORITY')
    authority.text = 'COPO'

    # Process FIELD_GROUPs from components
    for component_name in data_df['component_name'].unique():
        component_df = data_df[data_df['component_name'] == component_name].copy()
        restriction_type = component_df['component_restriction_type'].iloc[0] if 'component_restriction_type' in component_df else 'Any number or none of the fields'
        
        field_group = ET.SubElement(descriptor, 'FIELD_GROUP', restrictionType=restriction_type)
        
        group_name = ET.SubElement(field_group, 'NAME')
        group_name.text = component_name
        
        worksheet_label = helpers.get_worksheet_info(component_df, return_label=True)
        group_label = ET.SubElement(field_group, 'LABEL')
        group_label.text = worksheet_label

        group_description = ET.SubElement(field_group, 'DESCRIPTION')
        group_description.text = f"Fields under component '{worksheet_label}'"

        for _, row in component_df.iterrows():
            field_element = ET.SubElement(field_group, 'FIELD')

            label_element = ET.SubElement(field_element, 'LABEL')
            label_element.text = str(row.get('term_label', ''))

            name = ET.SubElement(field_element, 'NAME')
            name.text = str(row.get('term_name', ''))

            description = ET.SubElement(field_element, 'DESCRIPTION')
            description.text = str(row.get('term_description', ''))

            example = ET.SubElement(field_element, 'EXAMPLE')
            example.text = str(row.get('term_example', ''))
            
            namespace_prefix_value = row.get('namespace_prefix', '')
            
            if namespace_prefix_value:
                namespace = ET.SubElement(field_element, 'NAMESPACE')
                namespace.text = f"{row.get('namespace_prefix', '')}:{row.get('term_name', '')}"

            field_type = ET.SubElement(field_element, 'FIELD_TYPE')
            
            regex_value =row.get('term_regex', '')

            allowed_values = allowed_values_dict.get(row.get('term_name', ''), [])

            if regex_value:
                text_field = ET.SubElement(field_type, 'TEXT_FIELD')
                regex = ET.SubElement(text_field, 'REGEX_VALUE')
                regex.text = regex_value
            else:
                field_type_value = row.get('term_type', 'TEXT_FIELD')

                if field_type_value == 'TEXT_FIELD':
                    ET.SubElement(field_type, 'TEXT_FIELD')

            if allowed_values:
                allowed_values.sort() # Sort the allowed values
                
                choice_field = ET.SubElement(field_type, 'TEXT_CHOICE_FIELD')

                for value in allowed_values:
                    text_value = ET.SubElement(choice_field, 'TEXT_VALUE')
                    value_element = ET.SubElement(text_value, 'VALUE')
                    value_element.text = str(value)

            mandatory = ET.SubElement(field_element, 'MANDATORY')
            mandatory.text = str('mandatory' if row.get(version_column_name, '') == 'M' else 'optional')

            multiplicity = ET.SubElement(field_element, 'CARDINALITY')
            multiplicity.text = str(row.get('term_cardinality', 'single'))

    # Write XML file
    tree = ET.ElementTree(checklist_set)
    
    try:
        # Check if output_file_path is a valid file path (str or bytes)
        if not isinstance(output_file_path, (str, bytes)):
            raise TypeError(
                f"Expected a file path (str/bytes), got {type(output_file_path)} for '{output_file_path}'"
            )
        
        # Ensure the directory exists
        dir_path = os.path.dirname(output_file_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        
        # Convert XML tree to a string
        xml_str = ET.tostring(checklist_set, encoding='utf-8')

        # Prettify XML using minidom
        parsed_xml = xml.dom.minidom.parseString(xml_str)
        pretty_xml_str = parsed_xml.toprettyxml(indent="  ")  

        # Write formatted XML to file
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(pretty_xml_str)
        
        print(f"'{file_name}' created!")
    except Exception as e:
        raise IOError(f"Failed to write XML to {output_file_path}: {e}")

def extract_components_to_html(element):
    '''
    This function extracts components from an spreadsheet file and writes them to an spreadsheet file
    based on the components defined in the element dictionary
    It locks specific cells in each sheet and applies dropdown lists where necessary.

    Parameters:
    element (dict): A dictionary containing the following:
        - data_df (DataFrame): Data from the 'data' worksheet.
        - allowed_values_dict (dict): Mapping of allowed values for dropdowns.
        - output_file_path (str): The path to the output spreadsheet file.
        - standard_name (str): Namespace prefix (e.g. 'dwc', 'mixs', 'tol').
        - version_column_name (str): The name of the version column in the data_df.
    '''
    try:
        data_df = element['data_df']
        allowed_values_dict = element['allowed_values_dict']
        output_file_path = element['output_file_path']
        standard_name = element['standard_name']
        version_column_name = element['version_column_name']

        # Ensure output directory exists
        directory_path = os.path.dirname(output_file_path)
        os.makedirs(directory_path, exist_ok=True)

        # Process FIELD_GROUPs from components
        components = []

        for component_name in data_df['component_name'].unique():
            component_df = data_df[data_df['component_name'] == component_name].copy()

            group_label = helpers.get_worksheet_info(component_df, return_label=True)
            component_dict = {
                'group_name': component_name,
                'group_label': group_label,
                'group_description': f"Fields under component '{group_label}'.",
                'fields': []
            }

            for _, row in component_df.iterrows():
                allowed_values = allowed_values_dict.get(row.get('term_name', ''), [])
                namespace = f"{row.get('namespace_prefix', '')}:{row.get('term_name', '')}"
                namespace = namespace[:-1] if namespace.endswith(':') else namespace

                current_field = {
                    "label": row.get("term_label", ""),
                    "name": row.get("term_name", ""),
                    "description": row.get("term_description", ""),
                    "example": helpers.convert_datetime(row.get("term_example", "")),
                    "regex": row.get("term_regex", ""),
                    "namespace": namespace,
                    "mandatory": (
                        "mandatory"
                        if row.get(version_column_name, "") == "M"
                        else "optional"
                    ),
                    "reference": row.get("term_reference", ""),
                }

                if allowed_values:
                    allowed_values.sort() # Sort the allowed values
                    current_field['allowed_values'] = allowed_values

                component_dict['fields'].append(current_field)

            components.append(component_dict)

        # Render HTML using Jinja2 template
        environment = Environment(loader=FileSystemLoader('templates/'))
        fields_template = environment.get_template('fields_template.html')

        standards = {value['standard_name']:value['standard_label']for value in helpers.CHECKLISTS_DICT.values()}
        technologies = {value['technology_name']:value['technology_label']for value in helpers.CHECKLISTS_DICT.values()}

        output_file_name_dict = {
            f"{value['output_file_name']}_{helpers.SCHEMA_VERSION}.html": helpers.VersionData(
                value["technology_name"],
                value["technology_label"],
                value["standard_name"],
                value["standard_label"],
                value["version_description"],
            )
            for value in helpers.CHECKLISTS_DICT.values()
        }

        context = {'components': components, 'standards': standards, 'technologies': technologies, 'output_data':output_file_name_dict, 'version': helpers.SCHEMA_VERSION }

        with open(output_file_path, mode='w', encoding='utf-8') as fields:
            fields.write(fields_template.render(context))
    except Exception as e:
        raise RuntimeError(f'An error occurred: {e}')

def extract_and_convert_schema(standard=None, format_type=None):
    '''
    Extract and convert schema to multiple formats: XLSX, JSON, XML, and HTML.
    If a specific format_type is provided, only that format is processed.
    '''
    # Check if schema base input file is valid
    helpers.validate_schema_file()
    
    # Get dataframe and allowed values from spreadsheet file
    data_df, allowed_values_dict = helpers.read_xlsx_data()
    
    for checklist in helpers.CHECKLISTS_DICT.values():
        # If a specific standard is provided, skip unrelated entries
        if standard and standard != checklist['standard_name']:
            continue
        
        # Populate the element dictionary
        element = {
            'allowed_values_dict': allowed_values_dict,
            'data_df': data_df,
            'version_column_name': checklist['version_column_name'],
            'version_column_label': checklist['version_column_label'],
            'version_description': checklist['version_description'],
            'standard_name': checklist['standard_name'],
            'standard_label': checklist['standard_label'],
            'technology_name': checklist['technology_name'],
            'technology_label': checklist['technology_label'],
            'file_path': helpers.SCHEMA_FILE_PATH,
            'output_file_name': f"{checklist['output_file_name']}_{helpers.SCHEMA_VERSION}"
        }
        
        # Filter dataframe by namespace prefix name and schema name
        element['data_df'] = helpers.filter_data_frame(element)
        
        # Skip if the filtered data frame is empty
        if element['data_df'].empty:
            print(f"No data found for '{element['standard_name']}' standard and '{element['technology_name']}' technology. Skipping...")
            continue
              
        # Process only the specified format, if provided
        display_message = "\n*-Generating  '{format_type}' file using '{standard_name}'  standard and '{technology_name}' technology-*"
        if format_type:
            print(display_message.format(
                format_type=format_type,
                standard_name=element['standard_name'],
                technology_name=element['technology_name']
            ))        

            if format_type in helpers.FORMATS:
                handle_format(element, format_type)
            else:
                print(f'Invalid format_type: {format_type}. Skipping...')
            continue # Skip to the next iteration
        
        # Process all formats if no specific format is provided
        for f_type in helpers.FORMATS:
            print(display_message.format(
                format_type=f_type,
                standard_name=element['standard_name'],
                technology_name=element['technology_name']
            ))
            handle_format(element, f_type)

if __name__ == '__main__':
    args = sys.argv

    # Check for correct number of arguments
    if len(args) not in [1, 2]:
        print('Usage:')
        print(' 1. python convert.py : Extract components using all namespaces')
        print(' 2. python convert.py dwc: Extract components using "dwc" namespace. Other namespace prefixes that can be used are - "mixs" and "tol"')
        print(' 3. python convert.py html: Extract components using "html" format. Other formats that can be used are - "xlsx", "json, "xml"')
        sys.exit(1)
    elif len(args) == 1:
        # If no arguments are provided
        # Remove 'dist/checklists' directory if it exists
        helpers.remove_dist_directory()
        
        # Extract schema data and convert it into multiple formats for all mapping
        print(f'\n_________\n\n--Extracting \'{helpers.SCHEMA_FILE_PATH}\'--\n')
            
        helpers.get_checklists_from_xlsx_file()
        extract_and_convert_schema()      
    elif len(args) == 2:
        # If only namespace prefix is provided
        argument = args[1]
        
        helpers.get_checklists_from_xlsx_file()
        
        standards = [checklist['standard_name'] for checklist in helpers.CHECKLISTS_DICT.values()]
        
        if not (argument in helpers.FORMATS or argument in standards):
            print(f'Invalid argument: {argument}')
            sys.exit(1)
        
        # Remove 'dist/checklists' directory if it exists
        helpers.remove_dist_directory()
        
        # Extract schema data and convert it into multiple formats for all mapping for the given namespace prefix
        print(f'\n_________\n\n--Extracting \'{helpers.SCHEMA_FILE_PATH}\'--\n')
        
        # Get schema names from the spreadsheet file
        helpers.get_checklists_from_xlsx_file()
        
        if argument in standards:
            standard = argument
            print(f'\n*-With \'{standard}\' standard-*\n')
            extract_and_convert_schema(standard=standard)
            
        if argument in helpers.FORMATS:
            format_type = argument
            extract_and_convert_schema(format_type=format_type)
