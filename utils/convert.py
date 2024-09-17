from io import BytesIO
from openpyxl.utils import get_column_letter
import json
import os
import numpy as np
import pandas as pd
import sys
import xlsxwriter
import xml.etree.ElementTree as ET

def extract_components_to_excel(json_data, output_file, termset):
    """
    This function extracts components from a JSON file and writes them to an Excel file.

    Parameters:
    json_data (str): The path to the JSON file.
    output_file (str): The path to the output Excel file.

    The function first opens and reads the JSON file, then gets the Darwin Core (DwC) fields.
    It finds the 'sample' component in the JSON data and extends its fields with the DwC fields.
    The updated JSON data is then written to a new JSON file 'schemas/joint.json'.
    Finally, the function writes the components from the JSON data to the Excel file. Each component is written to a separate sheet.
    The column names in the Excel file are the keys from the fields of the component.
    The ExcelWriter object is autofitted to adjust the column widths in the Excel file.
    """
    with open(json_data, 'r') as json_file:
        data_dict = json.loads(json_file.read())

    dwc = get_dwc_fields(termset=termset)
    sample = next(d for d in data_dict["components"] if d["component"] == "sample")
    sample["fields"].extend(dwc)

    output_core_xlsx = output_file.replace(".json", "_core.xlsx").replace(".xlsx", "_core.xlsx").replace("schemas/", "dist/checklists/xlsx/")

   
    bytesIO = BytesIO()

    with pd.ExcelWriter(bytesIO, engine='xlsxwriter', mode='w') as writer:
        for component in data_dict['components']:
            column_names = [get_heading(key) for key in component["fields"]]
            df = pd.DataFrame(columns=column_names)

            # Remove NaNs columns (if any rows are present)
            if not df.empty:
                df.dropna(axis=1, how='all', inplace=True)

            # Save the DataFrame to an Excel file
            df.to_excel(writer, sheet_name=component['component'], index=False, header=True)

            # Get the column validation
            column_validation = get_validation(component)

            # Apply a dropdown list to the desired columns
            apply_dropdown_list(component, df, column_validation, writer)
          
        # Apply autofit to all sheets
        autofit_all_sheets(writer)

    # Save to output file
    with open(output_core_xlsx, 'wb') as f:
        f.write(bytesIO.getvalue())

def extract_components_to_json(json_data, output_file, termset):
    output_core = output_file.replace(".json", "_core.json").replace(".xlsx", "_core.json").replace("schemas/", "dist/checklists/json/")

    with open(json_data, 'r') as json_file:
        data_dict = json.loads(json_file.read())


    with open(output_core, "w") as joint_json:
        joint_json.write(json.dumps(data_dict))

def extract_components_to_xml(json_data, output_file, termset):
    """
    This function extracts components from a JSON file and writes them to an XML file.

    Parameters:
    json_data (str): The path to the JSON file.
    output_file (str): The path to the output XML file.

    The function first opens and reads the JSON file, then gets the Darwin Core (DwC) fields.
    It finds the 'sample' component in the JSON data and extends its fields with the DwC fields.
    The updated JSON data is then written to a new XML file.
    """

    CHECKLIST_MAPPING = {
        'SCRNASEQ':{
            'accession': 'SCRNASEQ1',
            'label': 'COPO Single Cell RNA-Sequencing Checklist',
            'name': 'COPO Single Cell RNA-Sequencing Checklist',
            'description': 'Minimum information to standardise metadata related to samples used in RNA seq experiments...',
            'checklistType': 'reads'
        },
        'SPATFISH':{
            'accession': 'SPATIMG1',
            'label': 'COPO Spatial Transcriptomics Image Checklist',
            'name': 'COPO Spatial Transcriptomics Image Checklist',
            'description': 'Minimum information to standardise metadata related to samples used in RNA seq experiments. Useful for downstream services to select RNA-Seq read data for appropriate alignment processing and display. Also useful for external users to select RNA-Seq read files, their alignments, and structured metadata describing the source material.',
            'checklistType': 'image'
        },
        'SPATSEQ':{
            'accession': 'SPATSEQ1',
            'label': 'COPO Spatial Transcriptomics Sequencing Checklist',
            'name': 'COPO Spatial Transcriptomics Sequencing Checklist',
            'description': 'Minimum information to standardise metadata related to samples used in RNA seq experiments. Useful for downstream services to select RNA-Seq read data for appropriate alignment processing and display. Also useful for external users to select RNA-Seq read files, their alignments, and structured metadata describing the source material.',
            'checklistType': 'reads'
        }
    }

    # Read JSON data
    with open(json_data, 'r') as json_file:
        data_dict = json.loads(json_file.read())

    dwc = get_dwc_fields(termset=termset)
    sample = next(d for d in data_dict["components"] if d["component"] == "sample")
    sample["fields"].extend(dwc)

    output_xml = output_file.replace(".json", "_core.xml").replace(".xlsx", "_core.xml").replace(".xlsx", "_core.xml").replace("schemas/", "dist/checklists/xml/")

    checklist_type_abbreviation = output_xml.split('/')[-1].replace('_core.xml', '').replace(f'_{termset}.xml', '').replace('_','').upper()
    accession = CHECKLIST_MAPPING.get(checklist_type_abbreviation,'').get('accession', '')
    checklist_type = CHECKLIST_MAPPING.get(checklist_type_abbreviation,'').get('checklistType', '')
    label = CHECKLIST_MAPPING.get(checklist_type_abbreviation,'').get('label', '')
    description = CHECKLIST_MAPPING.get(checklist_type_abbreviation,'').get('description', '')

    # Create root element
    checklist_set = ET.Element("CHECKLIST_SET")

    # Create checklist element
    checklist = ET.SubElement(checklist_set, "CHECKLIST", accession=accession, checklistType=checklist_type)

    # Create IDENTIFIERS
    identifiers = ET.SubElement(checklist, "IDENTIFIERS")
    primary_id = ET.SubElement(identifiers, "PRIMARY_ID")
    primary_id.text = accession

    # Create DESCRIPTOR
    descriptor = ET.SubElement(checklist, "DESCRIPTOR")

    # Add static elements to descriptor
    label = ET.SubElement(descriptor, "LABEL")
    label.text = label

    name = ET.SubElement(descriptor, "NAME")
    name.text = name

    description = ET.SubElement(descriptor, "DESCRIPTION")
    description.text = description

    authority = ET.SubElement(descriptor, "AUTHORITY")
    authority.text = "COPO"

    # Process FIELD_GROUPs from components
    for component in data_dict['components']:
        field_label_mapping = get_label_from_field_mapping(component)

        # Get the component validation
        component_validation = get_validation(component)

        field_group = ET.SubElement(descriptor, "FIELD_GROUP", restrictionType=component.get('restriction_type', 'Any number or none of the fields'))
        
        group_name = ET.SubElement(field_group, "NAME")
        group_name.text = component.get('component', '')

        group_description = ET.SubElement(field_group, "DESCRIPTION")
        group_description.text = component.get('description', '')

        for field_dict in component.get('fields', []):
            for field, value_dict in field_dict.items():
                if field in component_validation:
                    field_element = ET.SubElement(field_group, "FIELD")

                    label = ET.SubElement(field_element, "LABEL")
                    label.text = field_label_mapping.get(field,'')

                    name = ET.SubElement(field_element, "NAME")
                    name.text = field

                    description = ET.SubElement(field_element, "DESCRIPTION")
                    description.text = field_dict.get(field,'').get('description', '')

                    field_type = ET.SubElement(field_element, "FIELD_TYPE")
                    
                    regex_value = field_dict.get(field,'').get('regex', '')

                    if regex_value:
                        text_field = ET.SubElement(field_type, "TEXT_FIELD")
                        regex = ET.SubElement(text_field, "REGEX_VALUE")
                        regex.text = regex_value
                    else:
                        field_type_value = field_dict.get(field,'').get('type', 'TEXT_FIELD')

                        if field_type_value == 'TEXT_FIELD':
                            ET.SubElement(field_type, "TEXT_FIELD")
                    
                    if field_dict.get(field,'').get('allowed_values', []):
                        choice_field = ET.SubElement(field_type, "TEXT_CHOICE_FIELD")

                        for value in field_dict.get(field,'').get('allowed_values', []):
                            text_value = ET.SubElement(choice_field, "TEXT_VALUE")
                            value_element = ET.SubElement(text_value, "VALUE")
                            value_element.text = value

                    mandatory = ET.SubElement(field_element, "MANDATORY")
                    mandatory.text = 'mandatory' if field_dict.get(field,'').get('required', False) else 'optional'

                    multiplicity = ET.SubElement(field_element, "MULTIPLICITY")
                    multiplicity.text = field_dict.get(field,'').get('multiplicity', 'single')

    # Create and write XML file
    tree = ET.ElementTree(checklist_set)
    tree.write(output_xml, encoding='utf-8', xml_declaration=True)

def get_heading(key):
    fieldset = list(key.keys())[0]
    return key.get(fieldset, {}).get("label", fieldset)

def get_validation(component):
    field_validation = {}

    for element in component["fields"]:
        for field, valueDict in element.items():
            label = valueDict.pop('label','') if 'label' in valueDict else field
        field_validation[label] = valueDict

    return field_validation

def get_label_from_field_mapping(component):
    label_mapping = {}

    for element in component['fields']:
        for field, valueDict in element.items():
            label = valueDict.pop('label','') if 'label' in valueDict else field
            label_mapping[field] = label
    return label_mapping

def autofit_all_sheets(writer):
    for sheet in writer.sheets.values():
        sheet.autofit()

def get_dwc_fields(termset="extended"):
    """
    This function reads a CSV file and a JSON file, filters the data from the CSV file based on certain conditions,
    and returns a list of dictionaries representing the filtered data.

    The CSV file 'schemas/dwc.csv' contains data with various fields. The JSON file 'schemas/exclusions.json' contains
    a list of labels that should be excluded from the final output.

    The function first reads the CSV file using pandas and loads the JSON file. It then filters the data from the CSV file
    to include only those rows where the 'status' field is either 'recommended' or 'required'. It also excludes any rows
    where the 'label' field is in the list of excluded labels from the JSON file.

    For each of the remaining rows, it creates a dictionary using the 'create_field' function and adds it to the output list.

    Returns:
        out (list): A list of dictionaries representing the filtered data from the CSV file.
    """
    # Read the CSV file
    orig = pd.read_csv("schemas/dwc.csv")

    # Load the JSON file
    with open("schemas/exclusions.json") as excluded_json:
        excluded = json.loads(excluded_json.read())["excluded"]

    # Filter the data from the CSV file
    filtered = orig[(orig.status == "recommended")]

    # Create the output list

    if termset == "extended":
        out = [create_field(line) for _, line in filtered.iterrows()]
    elif termset == "core":
        out = [create_field(line) for _, line in filtered.iterrows() if
               line["term_localName"] in [item['name'] for item in excluded if item['set'] == "core"]]
    else:
        sys.exit("Invalid termset. Please use 'core' or 'extended' as termset.")
    return out

def create_field(line):
    return {line["term_localName"]: {"reference": line["iri"], "required": False, "type": "string"}}

def get_excel_data_validation_from_regex(regex, column_letter):
    # Define a mapping from regex patterns to Excel custom validation formulas
    REGEX_TO_EXCEL_DATA_VALIDATION_MAPPING = {
        '^[a-zA-Z0-9]+$': f'AND(LEN({column_letter}2)>0, {column_letter}2=TEXTJOIN("", TRUE, IF(ISNUMBER(FIND(MID({column_letter}2, ROW(INDIRECT("1:"&LEN({column_letter}2))), 1), "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")), MID({column_letter}2, ROW(INDIRECT("1:"&LEN({column_letter}2))), 1), "")))',
        '^[a-zA-Z]+$': f'AND(LEN({column_letter}2)>0, EXACT({column_letter}2, LOWER({column_letter}2)), {column_letter}2=SUBSTITUTE({column_letter}2, " ", ""))',
        '^[0-9]{4}-[0-9]{2}-[0-9]{2}$': f'AND(LEN({column_letter}2)>0, {column_letter}2=SUBSTITUTE(SUBSTITUTE({column_letter}2, "-", ""), " ", ""), ISNUMBER(SUBSTITUTE({column_letter}2, "-", "") + 0))',
        '^[-+]?([1-8]?\\d(\\.\\d+)?|90(\\.0+)?)$': f'AND(LEN({column_letter}2)>0, {column_letter}2=SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE({column_letter}2, "-", ""), "+", ""), ".", ""), " ", ""), ISNUMBER(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE({column_letter}2, "-", ""), "+", ""), ".", "") + 0))',
        '^[\\w-\\.]+@([\\w-]+\\.)+[\\w-]{2,4}$': f'AND(ISNUMBER(FIND("@", {column_letter}2)), FIND(".", {column_letter}2, FIND("@", {column_letter}2)) > FIND("@", {column_letter}2))'
    }

    # Return the corresponding Excel formula or None if regex is not in the mapping
    return REGEX_TO_EXCEL_DATA_VALIDATION_MAPPING.get(regex, None)

def apply_dropdown_list(component, dataframe, column_validation, pandas_writer):
    sheet_name = component['component']
    fields = component['fields']

    sheet = pandas_writer.sheets[sheet_name]
    workbook = pandas_writer.book

    # Create a hidden sheet for long dropdown lists
    hidden_sheet_name = 'HiddenDropdowns'
    hidden_sheet = workbook.get_worksheet_by_name(hidden_sheet_name)

    if not hidden_sheet:
        hidden_sheet = workbook.add_worksheet(hidden_sheet_name)
        hidden_sheet.hide()
    else:
        hidden_sheet = workbook.get_worksheet_by_name(hidden_sheet_name)

    # Check for duplicate columns
    if dataframe.columns.duplicated().any():
        print("Duplicate column names found:", dataframe.columns[dataframe.columns.duplicated()])
        # Remove duplicates
        dataframe = dataframe.loc[:, ~dataframe.columns.duplicated()]
    
    for column_name in dataframe.columns:
        if column_name in column_validation:
            is_field_required = column_validation[column_name].get('required', False)
            dropdown_list = column_validation[column_name].get('allowed_values', [])
            error_message = column_validation[column_name].get('error', '')
            field_type = column_validation[column_name].get('type', '')
            regex = column_validation[column_name].get('regex', '')

            # Get MS Excel official column header letter
            # Indexing starts at 0 by default but in this case, it should start at 1 so increment by 1
            column_index = dataframe.columns.get_loc(column_name)

            column_letter = get_column_letter(column_index + 1)

            # Get first row to the last row in a column 
            row_start_end = f'{column_letter}2:{column_letter}101'
            
            # Apply data formula to the column if regex is provided
            if regex:
                validation_formula = get_excel_data_validation_from_regex(regex, column_letter)
                if validation_formula:
                    sheet.data_validation(row_start_end, {'validate': 'custom', 'value': validation_formula, 'input_message': 'Invalid input', 'error_message': error_message})

            # Apply the dropdown list to the column
            if dropdown_list:
                dropdown_list = list(set(dropdown_list)) # Remove duplicates

                # Capitalise the first letter of each word in the list and replace underscores with spaces
                dropdown_list = [i.title().replace('_', ' ') for i in dropdown_list]
                dropdown_list.sort() # Sort the list in ascending order
                number_of_characters = sum(len(i) for i in dropdown_list)

                if number_of_characters >= 255:
                    print('The dropdown list is too long for Excel to handle. Please reduce the number of items in the list.')

                    for index, val in enumerate(dropdown_list, start=2):  # Start from row 2 to leave row 1 for headers if needed
                        hidden_sheet.write(f'{column_letter}{index}', val)

                    # Create a range reference for the hidden sheet
                    data_validation_range = f'={hidden_sheet_name}!${column_letter}$2:${column_letter}${index}'
                    sheet.data_validation(row_start_end, {'validate': 'list', 'source': data_validation_range, 'input_message': 'Choose from the list'})
                else:
                    sheet.data_validation(row_start_end, {'validate': 'list', 'source': dropdown_list, 'input_message': 'Choose from the list'})


if __name__ == '__main__':
    args = sys.argv

    if len(args) != 4:
        print("Usage: convert.py <json_file> <output_file> <termset>")
        ys.exit(1)  # Exit the script with an error code

    json_file = args[1]
    output_file = args[2]
    termset = args[3]

    extract_components_to_excel(json_file, output_file, termset)
    extract_components_to_json(json_file, output_file, termset)
    extract_components_to_xml(json_file, output_file, termset)
