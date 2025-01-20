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

def extract_components_to_excel(element):
    '''
    This function extracts components from an Excel file and writes them to an Excel file
    based on the components defined in the element dictionary
    It locks specific cells in each sheet and applies dropdown lists where necessary.

    Parameters:
    element (dict): A dictionary containing the following:
        - data_df (DataFrame): Data from the 'data' worksheet.
        - allowed_values_dict (dict): Mapping of allowed values for dropdowns.
        - output_file_path (str): The path to the output Excel file.
        - termset (str): Term set name (e.g., 'core', 'extended').
        - namespace_prefix (str): Namespace name (e.g. 'dwc', 'mixs', 'tol').
    '''
    data_df = element['data_df']
    allowed_values_dict = element['allowed_values_dict']
    output_file_path = element['output_file_path']
    termset = element['termset']
    namespace_prefix = element['namespace_prefix']
    
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

        # Iterate through unique components
        for component_name in data_df['component_name'].unique():
            component_df = data_df[data_df['component_name'] == component_name].copy()
            
            # Get the label of the terms as the column names from the component DataFrame
            column_names = component_df['term_label'].tolist()

            # If there are no fields for this component, skip it
            if not column_names:
                continue
            
            # Prepare DataFrame for writing to Excel
            df = pd.DataFrame(columns=column_names)
            
            # Extract metadata for formatting and validation
            required_columns = helpers.get_required_columns(component_df, namespace_prefix, termset)
            col_desc_eg = helpers.get_col_desc_eg(component_df, namespace_prefix, termset)

            # Remove NaNs columns (if any rows are present)
            if not df.empty:
                df.dropna(axis=1, how='all', inplace=True)

            # Write the DataFrame to an Excel sheet
            sheet_name = component_df['component_label'].iloc[0]
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
            helpers.apply_data_validation(component_df, df, writer, namespace_prefix, allowed_values_dict)

        # Apply autofit to all sheets
        helpers.autofit_all_sheets(writer)

    # Save to output file
    directory_path = os.path.dirname(output_file_path) # Get the directory path
    os.makedirs(directory_path, exist_ok=True) # Create output directory if it does not exist
    file_name = os.path.basename(output_file_path)

    with open(output_file_path, 'wb') as f:
        f.write(bytesIO.getvalue())
    
    print(f'{file_name} created!')

def extract_components_to_json(element):
    data_df = element['data_df']
    allowed_values_dict = element['allowed_values_dict']
    output_file_path = element['output_file_path']
    termset = element['termset']
    namespace_prefix = element['namespace_prefix']
    
    json_data = helpers.get_base_schema_json(data_df, allowed_values_dict, namespace_prefix=namespace_prefix, termset=termset)
    
    # Write JSON data to a file
    helpers.generate_json_file(json_data, output_file_path)

def extract_components_to_xml(element):
    '''
    This function extracts components from an Excel file and writes them to an Excel file
    based on the components defined in the element dictionary
    It locks specific cells in each sheet and applies dropdown lists where necessary.

    Parameters:
    element (dict): A dictionary containing the following:
        - data_df (DataFrame): Data from the 'data' worksheet.
        - allowed_values_dict (dict): Mapping of allowed values for dropdowns.
        - output_file_path (str): The path to the output Excel file.
        - termset (str): Term set name (e.g., 'core', 'extended').
        - namespace_prefix (str): Namespace prefix (e.g. 'dwc', 'mixs', 'tol').
    '''
    # Extract parameters
    data_df = element['data_df']
    allowed_values_dict = element['allowed_values_dict']
    output_file_path = element['output_file_path']
    termset = element['termset']
    namespace_prefix = element['namespace_prefix']

    # Ensure the output directory exists
    directory_path = os.path.dirname(output_file_path) # Get the directory path
    os.makedirs(directory_path, exist_ok=True) # Create output directory if it does not exist
    file_name = os.path.basename(output_file_path)

    # Extract checklist type details
    # Get the file name without the extension for the abbreviation

    # Check if the file ends with any of the extensions in FORMATS and remove it
    for ext in helpers.FORMATS.values():
        if file_name.endswith(ext):
            file_name = file_name[:-len(ext)]  # Remove the extension
            break  # Exit loop once the extension is found and removed
    
    checklist_type_abbreviation = file_name.replace('base', '') \
    .replace(termset,'') \
    .replace(namespace_prefix,'') \
    .replace('_','').upper()
    
    accession = helpers.CHECKLIST_MAPPING.get(checklist_type_abbreviation, '').get('accession', '')
    checklist_type = helpers.CHECKLIST_MAPPING.get(checklist_type_abbreviation, '').get('checklistType', '')
    checklist_label = helpers.CHECKLIST_MAPPING.get(checklist_type_abbreviation, '').get('label', '')
    checklist_name = helpers.CHECKLIST_MAPPING.get(checklist_type_abbreviation, '').get('name', '')
    checklist_description = helpers.CHECKLIST_MAPPING.get(checklist_type_abbreviation, '').get('description', '')

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
        
        group_label = ET.SubElement(field_group, 'LABEL')
        group_label.text = component_df['component_label'].iloc[0]

        group_description = ET.SubElement(field_group, 'DESCRIPTION')
        group_description.text = f"Fields under component '{component_df['component_label'].iloc[0]}'."

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
            mandatory.text = str('mandatory' if row.get('term_required', False) else 'optional')

            multiplicity = ET.SubElement(field_element, 'CARDINALITY')
            multiplicity.text = str(row.get('term_cardinality', 'single'))

    # Write XML file
    tree = ET.ElementTree(checklist_set)
    
    try:
        # Check if output_file_path is a valid file path (str or bytes)
        if not isinstance(output_file_path, (str, bytes)):
            raise TypeError(
                f'Expected a file path (str/bytes), got {type(output_file_path)} for "{output_file_path}"'
            )
        
        # Ensure the directory exists
        dir_path = os.path.dirname(output_file_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        
        tree.write(output_file_path, encoding='utf-8', xml_declaration=True)
        print(f'{file_name} created!')
    except Exception as e:
        raise IOError(f"Failed to write XML to {output_file_path}: {e}")
    

def extract_components_to_html(element):
    '''
    This function extracts components from an Excel file and writes them to an Excel file
    based on the components defined in the element dictionary
    It locks specific cells in each sheet and applies dropdown lists where necessary.

    Parameters:
    element (dict): A dictionary containing the following:
        - data_df (DataFrame): Data from the 'data' worksheet.
        - allowed_values_dict (dict): Mapping of allowed values for dropdowns.
        - output_file_path (str): The path to the output Excel file.
        - termset (str): Term set name (e.g., 'core', 'extended').
        - namespace_prefix (str): Namespace prefix (e.g. 'dwc', 'mixs', 'tol').
    '''
    try:
        data_df = element['data_df']
        allowed_values_dict = element['allowed_values_dict']
        output_file_path = element['output_file_path']
        termset = element['termset']
        namespace_prefix = element['namespace_prefix']

        # Ensure output directory exists
        directory_path = os.path.dirname(output_file_path)
        os.makedirs(directory_path, exist_ok=True)

        # Process FIELD_GROUPs from components
        components = []
        
        for component_name in data_df['component_name'].unique():
            component_df = data_df[data_df['component_name'] == component_name].copy()
            
            group_label = component_df['component_label'].iloc[0]
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
                    'label': row.get('term_label', ''),
                    'name': row.get('term_name', ''),
                    'description': row.get('term_description', ''),
                    'example': row.get('term_example', ''),
                    'regex': row.get('term_regex', ''),
                    'namespace': namespace,
                    'mandatory': 'mandatory' if row.get('term_required', False) else 'optional',
                    'reference': row.get('term_reference', '')
                }
                
                if allowed_values:
                    allowed_values.sort() # Sort the allowed values
                    current_field['allowed_values'] = allowed_values
                    
                component_dict['fields'].append(current_field)

            components.append(component_dict)

        # Render HTML using Jinja2 template
        environment = Environment(loader=FileSystemLoader('templates/'))
        fields_template = environment.get_template('fields_template.html')
        context = {'components': components}
        with open(output_file_path, mode='w', encoding='utf-8') as fields:
            fields.write(fields_template.render(context))
    except Exception as e:
        print(f'An error occurred: {e}')

def extract_and_convert_schema(file_path, termset, namespace_prefix):
    '''
    Extract and convert schema to multiple formats: Excel, JSON, XML, and HTML.
    '''
    
    # Get dataframe and allowed values from Excel file
    data_df, allowed_values_dict = helpers.read_excel_data(file_path, namespace_prefix, termset)
    
    # Define a base element dictionary
    element = {
        'data_df': data_df,
        'allowed_values_dict': allowed_values_dict,
        'termset': termset,
        'namespace_prefix': namespace_prefix
    }
    
    # Generate and extract components for each format
    for format_type, extension in helpers.FORMATS.items():
        element['output_file_path'] = helpers.generate_output_file_path(file_path, namespace_prefix, termset, input_extension=extension)

        match format_type:
            case 'excel':
                extract_components_to_excel(element)
            case 'json':
                extract_components_to_json(element)
            case 'xml':
                extract_components_to_xml(element)
            case 'html':
                extract_components_to_html(element)

if __name__ == '__main__':
    args = sys.argv

    # Check for correct number of arguments
    if len(args) not in [1, 4]:
        print('Usage:')
        print('  1. python convert.py : Extract components using all termsets and namespaces')
        print('  2. python convert.py <termset> : Extract components using a specific termset')
        print('  3. python convert.py <file_path> <termset> : Extract components from a provided Excel schema file with a specific termset')
        print('  4. python convert.py <file_path> <termset> <namespace_prefix>: Extract components from a provided Excel schema file with a specific termset and namespace prefix')
        sys.exit(1)

    # If no arguments are provided
    if len(args) == 1:
        # Remove 'dist/checklists' directory if it exists
        helpers.remove_dist_directory()
        
        # Get the JSON schema file paths
        for x in helpers.SCHEMA_FILE_PATHS:
            # Extract schema data and converts it into multiple formats for all mapping
            for termset in helpers.TERMSETS:
                print(f'\n_________\n\n--Extracting \'{x}\' with \'{termset}\' termset--\n')
                for namespace_prefix in helpers.NAMESPACE_PREFIX_MAPPING_FILTERED:
                    print(f'\n*-With \'{namespace_prefix}\' namespace prefix-*\n')
                    extract_and_convert_schema(x, termset, namespace_prefix)
    elif len(args) == 2:
        # If only termset is provided
        termset = args[1]

        # Check if the termset provided is valid
        helpers.validate_argument(
            argument=termset,
            valid_arguments=helpers.TERMSETS,
            error=msg['error_msg_invalid_termset']
        )
        
        # Remove 'dist/checklists' directory if it exists
        helpers.remove_dist_directory()
        
        # Get the JSON schema file paths
        for x in helpers.SCHEMA_FILE_PATHS:
            # Extract schema data and converts it into multiple formats for all mapping
            print(f'\n_________\n\n--Extracting \'{x}\' with \'{termset}\' termset--\n')
            for namespace_prefix in helpers.NAMESPACE_PREFIX_MAPPING_FILTERED:
                print(f'\n*-With \'{namespace_prefix}\' namespace prefix-*\n')
                extract_and_convert_schema(x, termset, namespace_prefix)
    elif len(args) == 3:
        # If file_path, termset and namespace prefix are provided
        file_path = args[1]  # Path to the schema JSON file
        termset = args[2]

        # Check if the file path provided is valid
        helpers.validate_argument(
            argument=file_path,
            valid_arguments=helpers.SCHEMA_FILE_PATHS,
            error=msg['error_msg_invalid_file_path']
        )

        # Check if the termset provided is valid
        helpers.validate_argument(
            argument=termset,
            valid_arguments=helpers.TERMSETS,
            error=msg['error_msg_invalid_termset']
        )
        
        # Remove 'dist/checklists' directory if it exists
        helpers.remove_dist_directory()
        
        # Extract schema data and converts it into multiple formats for all mapping
        for namespace_prefix in helpers.NAMESPACE_PREFIX_MAPPING_FILTERED:
            extract_and_convert_schema(file_path, termset, namespace_prefix)
    elif len(args) == 4:
        file_path = args[1]
        termset = args[2]
        namespace_prefix = args[3]

        # Check if the file path provided is valid
        helpers.validate_argument(
            argument=file_path,
            valid_arguments=helpers.SCHEMA_FILE_PATHS,
            error=msg['error_msg_invalid_file_path']
        )

        # Check if the termset provided is valid
        helpers.validate_argument(
            argument=termset,
            valid_arguments=helpers.TERMSETS,
            error=msg['error_msg_invalid_termset']
        )
        
        # Check if the namespace prefix provided is valid
        helpers.validate_argument(
            argument=namespace_prefix,
            valid_arguments=helpers.NAMESPACE_PREFIX_MAPPING_FILTERED,
            error=msg['error_msg_invalid_standard']
        )
        
        # Remove 'dist/checklists' directory if it exists
        helpers.remove_dist_directory()
        
        # Extract schema data and converts it into multiple formats with a specific namespace prefix
        extract_and_convert_schema(file_path, termset, namespace_prefix)