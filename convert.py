from io import BytesIO
from jinja2 import Environment, FileSystemLoader
from openpyxl.utils import get_column_letter
from utils.helpers import MESSAGES as msg

import jinja2 as j2
import json
import numpy as np
import os
import pandas as pd
import shutil
import sys
import utils.helpers as helpers
import xlsxwriter
import xml.etree.ElementTree as ET

def extract_components_to_excel(data_dict, output_file_path, termset, standard):
    '''
    This function extracts components from a JSON file and writes them to an Excel file.
    It locks specific cells in each sheet and applies dropdown lists where necessary.

    Parameters:
    data_dict (dictionary): Data from the the JSON file.
    output_file_path (str): The path to the output Excel file.

    The function first opens and reads the JSON file, then gets the Darwin Core (DwC) fields.
    It finds the 'sample' component in the JSON data and extends its fields with the DwC fields.
    The updated JSON data is then written to a new JSON file 'schemas/joint.json'.
    Finally, the function writes the components from the JSON data to the Excel file. Each component is written to a separate sheet.
    The column names in the Excel file are the keys from the fields of the component.
    The ExcelWriter object is autofitted to adjust the column widths in the Excel file.
    '''

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

        for component in data_dict['components']:
            column_names = list(helpers.get_field_label_mapping(component, standard).keys())
            column_length = len(column_names)
            df = pd.DataFrame(columns=column_names)

            required_columns = helpers.get_required_columns(component, standard)
            col_desc_eg = helpers.get_col_desc_eg(component, standard)

            # Remove NaNs columns (if any rows are present)
            if not df.empty:
                df.dropna(axis=1, how='all', inplace=True)

            # Write the DataFrame to an Excel sheet
            sheet_name = helpers.convertStringToTitleCase(component['component'])
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
            
            # Apply dropdown list validation where required
            column_validation = helpers.get_validation(component, standard)
            helpers.apply_dropdown_list(component, df, column_validation, writer, standard)

        # Apply autofit to all sheets
        helpers.autofit_all_sheets(writer)

    # Save to output filex
    output_file_path = output_file_path.replace(f'{helpers.SCHEMA_BASE_DIR_PATH}/', f'dist/checklists/{termset}/xlsx/{standard}/')
    directory_path = os.path.dirname(output_file_path) # Get the directory path
    os.makedirs(directory_path, exist_ok=True) # Create output directory if it does not exist
    file_name = output_file_path.split('/')[-1]

    # Check if there's a conflicting directory with the same name as the file
    if os.path.isdir(output_file_path):
        print(f"Warning: A directory exists with the name '{output_file_path}'. Overwriting it.")
        shutil.rmtree(output_file_path)  # Remove the directory and its contents

    with open(output_file_path, 'wb') as f:
        f.write(bytesIO.getvalue())
    
    print(f'{file_name} created!')

def extract_components_to_json(data_dict, output_file_path, termset, standard):
    output_file_path = output_file_path.replace(f'{helpers.SCHEMA_BASE_DIR_PATH}/', f'dist/checklists/{termset}/json/{standard}/')

    # Write JSON data to a file
    helpers.generate_json_file(data_dict, output_file_path)

def extract_components_to_xml(data_dict, output_file_path, termset, standard):
    '''
    This function extracts components from a JSON file and writes them to an XML file.

    Parameters:
    data_dict (str): Data from the JSON file.
    output_file_path (str): The path to the output XML file.
    '''

    # Create output directory if it does not exist
    output_file_path = output_file_path.replace('.json', f'_{termset}.xml').replace('.xlsx', f'_{termset}.xml').replace(f'{helpers.SCHEMA_BASE_DIR_PATH}/', f'dist/checklists/{termset}/xml/{standard}/')
    directory_path = os.path.dirname(output_file_path) # Get the directory path
    os.makedirs(directory_path, exist_ok=True) # Create output directory if it does not exist
    file_name = output_file_path.split('/')[-1]

    # Check if there's a conflicting directory with the same name as the file
    if os.path.isdir(output_file_path):
        print(f"Warning: A directory exists with the name '{output_file_path}'. Overwriting it.")
        shutil.rmtree(output_file_path)  # Remove the directory and its contents

    # Prepare checklist type details
    checklist_type_abbreviation = file_name.replace(f'_{standard}_{termset}.xml', '').replace('_','').upper()
    accession = helpers.CHECKLIST_MAPPING.get(checklist_type_abbreviation,'').get('accession', '')
    checklist_type = helpers.CHECKLIST_MAPPING.get(checklist_type_abbreviation,'').get('checklistType', '')
    label = helpers.CHECKLIST_MAPPING.get(checklist_type_abbreviation,'').get('label', '')
    description = helpers.CHECKLIST_MAPPING.get(checklist_type_abbreviation,'').get('description', '')

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
    label.text = label

    name = ET.SubElement(descriptor, 'NAME')
    name.text = name

    description = ET.SubElement(descriptor, 'DESCRIPTION')
    description.text = description

    standard_element = ET.SubElement(descriptor, 'STANDARD')
    standard_element.text = standard

    authority = ET.SubElement(descriptor, 'AUTHORITY')
    authority.text = 'COPO'

    # Process FIELD_GROUPs from components
    for component in data_dict['components']:
        field_label_mapping = helpers.get_field_label_mapping(component, standard)
        group_label = helpers.convertStringToTitleCase(component.get('component', ''))

        # Get the component validation
        component_validation = helpers.get_validation(component, standard)

        field_group = ET.SubElement(descriptor, 'FIELD_GROUP', restrictionType=component.get('restriction_type', 'Any number or none of the fields'))
        
        group_label_element = ET.SubElement(field_group, 'LABEL')
        group_label_element.text = group_label

        group_name_element = ET.SubElement(field_group, 'NAME')
        group_name_element.text = component.get('component', '')

        group_description = ET.SubElement(field_group, 'DESCRIPTION')
        group_description.text = component.get('description', '')

        for field_dict in component.get('fields', []):
            for field, value_dict in field_dict.items():
                label = next((k for k, v in field_label_mapping.items() if v == field), '')
                data_dict = component_validation.get(label, str())

                if data_dict:
                    mapping_dict = data_dict.get('mapping', dict())

                    field_element = ET.SubElement(field_group, 'FIELD')

                    label_element = ET.SubElement(field_element, 'LABEL')
                    label_element.text = mapping_dict.get(standard, {}).get('label', str())

                    name = ET.SubElement(field_element, 'NAME')
                    name.text = mapping_dict.get(standard, {}).get('name', str())

                    description = ET.SubElement(field_element, 'DESCRIPTION')
                    description.text = data_dict.get('description', '')

                    example = ET.SubElement(field_element, 'EXAMPLE')
                    example.text = data_dict.get('example', '')

                    field_type = ET.SubElement(field_element, 'FIELD_TYPE')
                    
                    regex_value = data_dict.get('regex', '')

                    allowed_values = data_dict.get('default_map', {}).get('allowed_values', [])

                    is_field_required = data_dict.get('default_map', {}).get('required', False)

                    if regex_value:
                        text_field = ET.SubElement(field_type, 'TEXT_FIELD')
                        regex = ET.SubElement(text_field, 'REGEX_VALUE')
                        regex.text = regex_value
                    else:
                        field_type_value = data_dict.get('type', 'TEXT_FIELD')

                        if field_type_value == 'TEXT_FIELD':
                            ET.SubElement(field_type, 'TEXT_FIELD')

                    if allowed_values:
                        choice_field = ET.SubElement(field_type, 'TEXT_CHOICE_FIELD')

                        for value in allowed_values:
                            text_value = ET.SubElement(choice_field, 'TEXT_VALUE')
                            value_element = ET.SubElement(text_value, 'VALUE')
                            value_element.text = value

                    mandatory = ET.SubElement(field_element, 'MANDATORY')
                    mandatory.text = 'mandatory' if is_field_required else 'optional'

                    multiplicity = ET.SubElement(field_element, 'MULTIPLICITY')
                    multiplicity.text = data_dict.get('multiplicity', 'single')

    # Create and write XML file
    tree = ET.ElementTree(checklist_set)
    tree.write(output_file_path, encoding='utf-8', xml_declaration=True)

    print(f'{file_name} created!')

def extract_components_to_html(data_dict, output_file_path, termset, standard):
    '''
    This function extracts components from a JSON file and writes them to an HTML file.

    Parameters:
    data_dict (dict): Data from the JSON file.
    output_file_path (str): The path to the output HTML file.
    '''

    # Create output directory if it does not exist
    output_file_path = (
        output_file_path.replace('.json', f'_{termset}.html')
        .replace('.xlsx', f'_{termset}.html')
        .replace(f'{helpers.SCHEMA_BASE_DIR_PATH}/', f'dist/checklists/{termset}/html/{standard}/')
        .replace('.xml', '.html')
        .replace('/base', '')
    )
    directory_path = os.path.dirname(output_file_path)
    os.makedirs(directory_path, exist_ok=True)

    # Check if there's a conflicting directory with the same name as the file
    if os.path.isdir(output_file_path):
        print(f"Warning: A directory exists with the name '{output_file_path}'. Overwriting it.")
        shutil.rmtree(output_file_path)

    # Prepare checklist type details
    file_name = os.path.basename(output_file_path)
    checklist_type_abbreviation = file_name.replace(f'_{standard}_{termset}.html', '').replace('_', '').upper()
    checklist_info = helpers.CHECKLIST_MAPPING.get(checklist_type_abbreviation, {})
    accession = checklist_info.get('accession', '')
    checklist_type = checklist_info.get('checklistType', '')
    label = checklist_info.get('label', '')
    description = checklist_info.get('description', '')

    # Process FIELD_GROUPs from components
    components = []
    for component in data_dict['components']:
        group_label = helpers.convertStringToTitleCase(component.get('component', ''))
        component_dict = {
            "group_label": group_label,
            "group_name": component.get('component', ''),
            "group_description": component.get('description', ''),
            "fields": []
        }
        field_label_mapping = helpers.get_field_label_mapping(component, standard)
        component_validation = helpers.get_validation(component, standard)

        for field_dict in component.get('fields', []):
            for field, value_dict in field_dict.items():
                label = next((k for k, v in field_label_mapping.items() if v == field), '')
                data_dict = component_validation.get(label, {})

                if data_dict:
                    mapping_dict = data_dict.get('mapping', {})
                    default_map = data_dict.get('default_map', {})
                    reference = data_dict.get('default_map', {}).get('reference', '')
                    current_field = {
                        "label": mapping_dict.get(standard, {}).get('label', ''),
                        "name": mapping_dict.get(standard, {}).get('name', ''),
                        "description": data_dict.get('description', ''),
                        "example": data_dict.get('example', ''),
                        "regex": data_dict.get('regex', ''),
                        "allowed_values": default_map.get('allowed_values', []),
                        "mandatory": 'mandatory' if  default_map.get('required', False) else 'optional',
                        "multiplicity": data_dict.get('multiplicity', 'single'),
                        "reference": default_map.get('reference', '')

                    }
                    component_dict["fields"].append(current_field)
        components.append(component_dict)

    # Render HTML using Jinja2 template
    environment = Environment(loader=FileSystemLoader("templates"))
    fields_base_template = environment.get_template("base.html")
    context = {"components": components}
    with open(output_file_path, mode="w", encoding="utf-8") as fields:
        fields.write(fields_base_template.render(context))

def extract_and_convert_schema(json_schema_file_path, termset, standard):
    # Get fields based on the termset
    termset_fields = helpers.retrieve_data_by_termset(termset)

    # Update schema data with termset fields
    helpers.update_schema_with_termset_fields(json_schema_file_path, termset_fields, termset)

    # Read JSON schema data
    with open(json_schema_file_path, 'r') as schema_data:
        data_dict = json.loads(schema_data.read())

    # Add the termset fields to the schema for the 'sample' component
    sample = next(d for d in data_dict['components'] if d['component'] == 'sample')

    # Extend the 'sample' component fields with DwC fields and remove duplicates
    sample['fields'] = helpers.remove_duplicates(sample['fields'], termset_fields)

    # Extract components to formats
    extract_components_to_excel(data_dict, json_schema_file_path.replace('.json', f'_{standard}_{termset}.xlsx'), termset, standard)
    extract_components_to_json(data_dict, json_schema_file_path.replace('.json', f'_{standard}_{termset}.json'), termset, standard)
    extract_components_to_xml(data_dict, json_schema_file_path.replace('.json', f'_{standard}_{termset}.xml'), termset, standard)
    extract_components_to_html(data_dict, json_schema_file_path.replace('.json', f'_{standard}_{termset}.html'), termset, standard)

if __name__ == '__main__':
    args = sys.argv

    # Check for correct number of arguments
    if len(args) not in [1, 4]:
        print('Usage:')
        print('  1. python convert.py : Extract components using all termsets and standards')
        print('  2. python convert.py <termset> : Extract components using a specific termset')
        print('  3. python convert.py <json_schema_file_path> <termset> : Extract components from a provided JSON schema file with a specific termset')
        print('  4. python convert.py <json_schema_file_path> <termset> <standard>: Extract components from a provided JSON schema file with a specific termset and standard')
        sys.exit(1)

    # If no arguments are provided
    if len(args) == 1:
        # Get the JSON schema file paths
        for json_schema_file_path in helpers.SCHEMA_FILE_PATHS:
            # Extract schema data and converts it into multiple formats for all mapping
            for termset in helpers.TERMSETS:
                print(f'\n_________\n\n--Extracting "{json_schema_file_path}" with "{termset}" termset--\n')
                for standard in helpers.MAPPING:
                    print(f'\n*-With "{standard}" standard-*\n')
                    extract_and_convert_schema(json_schema_file_path, termset, standard)
    elif len(args) == 2:
        # If only termset is provided
        termset = args[1]

        # Check if the termset provided is valid
        helpers.validate_argument(
            argument=termset,
            valid_arguments=helpers.TERMSETS,
            error=msg['error_msg_invalid_termset']
        )
        
        # Get the JSON schema file paths
        for json_schema_file_path in helpers.SCHEMA_FILE_PATHS:
            # Extract schema data and converts it into multiple formats for all mapping
            print(f'\n_________\n\n--Extracting "{json_schema_file_path}" with "{termset}" termset--\n')
            for standard in helpers.MAPPING:
                print(f'\n*-With "{standard}" standard-*\n')
                extract_and_convert_schema(json_schema_file_path, termset, standard)
    elif len(args) == 3:
        # If json_schema_file_path, termset and standard are provided
        json_schema_file_path = args[1]  # Path to the schema JSON file
        termset = args[2]

        # Check if the file path provided is valid
        helpers.validate_argument(
            argument=json_schema_file_path,
            valid_arguments=helpers.SCHEMA_FILE_PATHS,
            error=msg['error_msg_invalid_file_path']
        )

        # Check if the termset provided is valid
        helpers.validate_argument(
            argument=termset,
            valid_arguments=helpers.TERMSETS,
            error=msg['error_msg_invalid_termset']
        )

        # Extract schema data and converts it into multiple formats for all mapping
        for standard in helpers.MAPPING:
            extract_and_convert_schema(json_schema_file_path, termset, standard)
    elif len(args) == 4:
        json_schema_file_path = args[1]
        termset = args[2]
        standard = args[3]

        # Check if the file path provided is valid
        helpers.validate_argument(
            argument=json_schema_file_path,
            valid_arguments=helpers.SCHEMA_FILE_PATHS,
            error=msg['error_msg_invalid_file_path']
        )

        # Check if the termset provided is valid
        helpers.validate_argument(
            argument=termset,
            valid_arguments=helpers.TERMSETS,
            error=msg['error_msg_invalid_termset']
        )
        
        # Check if the standard provided is valid
        helpers.validate_argument(
            argument=standard,
            valid_arguments=helpers.MAPPING,
            error=msg['error_msg_invalid_standard']
        )
        
        # Extract schema data and converts it into multiple formats with a specific standard
        extract_and_convert_schema(json_schema_file_path, termset, standard)