from openpyxl.utils import get_column_letter

import json
import os
import pandas as pd
import sys

# Helpers: Variables
EXCLUDED_FILES = ['exclusions.json', 'sample_fields_core.json', 'sample_fields_extended.json']

MAPPING = ['dwc', 'mixs', 'schemaorg', 'tol']

SCHEMA_BASE_DIR_PATH = 'schemas/base'

SCHEMA_FILE_PATHS = [f'{SCHEMA_BASE_DIR_PATH}/{filename}' for root, dirs, files in os.walk(SCHEMA_BASE_DIR_PATH) 
                        for filename in files if filename.endswith('.json') and 
                        filename not in EXCLUDED_FILES
                    ]

TERMSETS = ['core', 'extended']

# Helpers: Mappings
CHECKLIST_MAPPING = {
    'SCRNASEQ':{
        'accession': 'SCRNASEQ1',
        'label': 'COPO Single Cell RNA-Sequencing Checklist',
        'name': 'COPO Single Cell RNA-Sequencing Checklist',
        'description': 'Minimum information to standardise metadata related to samples used in RNA seq experiments...',
        'checklistType': 'reads'
    },
    'STXFISH':{
        'accession': 'STXIMG1',
        'label': 'COPO Spatial Transcriptomics Image Checklist',
        'name': 'COPO Spatial Transcriptomics Image Checklist',
        'description': 'Minimum information to standardise metadata related to samples used in RNA seq experiments. Useful for downstream services to select RNA-Seq read data for appropriate alignment processing and display. Also useful for external users to select RNA-Seq read files, their alignments, and structured metadata describing the source material.',
        'checklistType': 'image'
    },
    'STXSEQ':{
        'accession': 'STXSEQ1',
        'label': 'COPO Spatial Transcriptomics Sequencing Checklist',
        'name': 'COPO Spatial Transcriptomics Sequencing Checklist',
        'description': 'Minimum information to standardise metadata related to samples used in RNA seq experiments. Useful for downstream services to select RNA-Seq read data for appropriate alignment processing and display. Also useful for external users to select RNA-Seq read files, their alignments, and structured metadata describing the source material.',
        'checklistType': 'reads'
    }
}

MESSAGES = {
    'error_msg_invalid_file_path': f'Invalid .json schema file path. Please check the "{SCHEMA_BASE_DIR_PATH}" directory for available files',
    'error_msg_invalid_standard': f"""Invalid standard. Please use {' or '.join([f'"{term}"' for term in MAPPING])} as standard.""",
    'error_msg_invalid_termset': f"""Invalid termset. Please use {' or '.join([f'"{term}"' for term in TERMSETS])} as termset."""
}

# Helpers: Functions
def convertStringToTitleCase(text):
    # Convert given a string to title case/sentence case
    return text.title().replace('_', ' ')

def get_col_desc_eg(component, standard):
    field_validation = get_validation(component, standard)
    return {field: {'description': field_info.get('description', ''), 'example': field_info.get('example', '')} for field, field_info in field_validation.items()}

def generate_json_file(data, output_file_path):
    '''
    This function writes data to a JSON file.

    Parameters:
    data (dict): The data to write to the JSON file.
    output_file_path (str): The path to the JSON file.
    '''
    directory_path = os.path.dirname(output_file_path) # Get the directory path
    os.makedirs(directory_path, exist_ok=True) # Create output directory if it does not exist
    file_name = output_file_path.split('/')[-1]
    
    # Check if there's a conflicting directory with the same name as the file
    if os.path.isdir(output_file_path):
        print(f"Warning: A directory exists with the name '{output_file_path}'. Overwriting it.")
        shutil.rmtree(output_file_path)  # Remove the directory and its contents

    file_name = output_file_path.split('/')[-1]

    with open(output_file_path, 'w') as f:
        f.write(json.dumps(data, indent=2))

    print(f'{file_name} created!')

def get_validation(component, standard):
    field_validation = {}

    for element in component['fields']:
        for field, field_info in element.items():
            if field_info.get('mapped_manifests',{}).get(standard, False):
                # Get the default label and name from the 'schemaorg' 
                # standard if no label or name is provided for the standard
                default_label = field_info.get('default_map', {}).get('label', '')
                default_name = field_info.get('default_map', {}).get('name','')
                
                label = (
                    field_info.get('mapping', {}).get(standard, {}).get('label') or 
                    default_label or  convertStringToTitleCase(field)
                )

                name = (
                    field_info.get('mapping', {}).get(standard, {}).get('name') or
                    default_name or field
                )

                # Ensure the 'mapping' dictionary and the specific standard sub-dictionary exist
                field_info.setdefault('mapping', {}).setdefault(standard, {})

                # Assign the label and name values
                field_info['mapping'][standard]['label'] = label
                field_info['mapping'][standard]['name'] = name

                # Update field_validation with the label as the key
                field_validation[label] = field_info
    return field_validation

def get_field_label_mapping(component, standard):
    field_validation = get_validation(component, standard)
    label_mapping = {field: field_info.get('mapping',dict()).get(standard,str()).get('name', field) for field, field_info in field_validation.items()}
    return label_mapping

def get_required_columns(component, standard):
    field_validation = get_validation(component, standard)
    return [field for field, field_info in field_validation.items() if field_info.get('default_map', {}).get('required', False)]

def merge_row(worksheet, row, last_column_letter, merge_format):
    """
    Function to merge cells in a row, unmerging any existing merged cells in that row if necessary.
    
    Args:
        worksheet: The worksheet object where the merge operation should be applied.
        row: The row number where merging is to occur.
        last_column_letter: The last column letter up to which the merge should occur.
        merge_format: The format to apply to the merged range.
    """
    # Iterate through all the existing merge ranges to check if any conflicts exist
    merged_range = None
    # Check if there are any merged ranges
    if worksheet.merged_cells.get('ranges', dict()):  # Check if there are merged ranges
        for merge_range in worksheet.merged_cells.ranges:
            # Parse the merge range in the format 'A1:B1'
            start_cell, end_cell = merge_range.split(":")
            start_row = int(''.join(filter(str.isdigit, start_cell)))

            # If the row is the same as the one we're trying to merge
            if start_row == row:
                merged_range = (start_cell, end_cell)
                break

    try:
        # If the row is already merged, unmerge the conflicting range
        if merged_range:
            start_cell, end_cell = merged_range
            print(f'Row {row} is already merged between {start_cell} and {end_cell}. Undoing merge first.')
            worksheet.unmerge_range(f'{start_cell}:{end_cell}')
        
        # Proceed with merging the new range
        worksheet.merge_range(f'A{row}:{last_column_letter}{row}', 'FILL OUT INFORMATION BELOW THIS ROW', merge_format)

    except Exception as e:
        print(f'Error: {e}')

def retrieve_data_by_termset(termset):
    '''
    Retrieve dictionary data from a JSON file based on the specified termset.

    Parameters:
    termset (str): The termset to filter by, either 'extended' or 'core'.

    Returns:
    dict: A dictionary containing the fields that match the specified termset.
    '''
    if termset not in TERMSETS:
        sys.exit("Invalid termset. Please use 'core' or 'extended' as termset.")

    # Define the file path based on the termset
    file_path = f'schemas/{termset}/sample_fields_{termset}.json'
    
    # Read the JSON file
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print(f'File not found: {file_path}')
        return {}

    # Filter data based on the termset value
    filtered_data = {
        key: value
        for key, value in data.items()
        if value.get('termset') == termset
    }

    return filtered_data

def remove_duplicates(fields, new_fields):
   # Create a dictionary to hold unique fields by their key (e.g., 'sample_id')
    unique_fields = {}

    # Add existing fields to the unique_fields dictionary
    for field in fields:
        # Extract the key and the field data
        field_key = list(field.keys())[0]
        unique_fields[field_key] = field[field_key]

    # Add or update new fields from new_fields
    for new_field_key, new_field_value in new_fields.items():
        unique_fields[new_field_key] = new_field_value

    # Convert back to the original list of dictionaries format
    return [{key: value} for key, value in unique_fields.items()]

def update_schema_with_termset_fields(json_schema_file_path, termset_fields, termset):
    file_name = os.path.basename(json_schema_file_path).replace('.json', '')
    
    if not termset_fields:
        print(f'No termset fields found for {termset}')
        return

    # Load the current schema data
    with open(json_schema_file_path, 'r') as f:
        data = json.load(f)

    # Retrieve components from the JSON schema data
    components = data.get('components', [])

    # Update each component with matching termset fields
    for component in components:
        for field in component.get('fields', []):
            for key, attributes in field.items():
                # Check if the key exists in termset_fields
                if key in termset_fields:
                    termset_info = termset_fields[key]
                    schema_types = termset_info.get('schema_types', [])

                    # Update the field if the schema file name is in schema_types
                    if file_name in schema_types:
                        # Remove schema_types and termset to avoid including it in the updated schema
                        termset_info.pop('schema_types', None)
                        termset_info.pop('termset', None)

                        # Update the field attributes with termset_info data
                        field[key] = termset_info

    # Save the updated data to a new JSON file
    updated_data = {'components': components}

    output_file_name = f'{file_name}_{termset}.json'
    output_file_path = os.path.join('schemas', termset, output_file_name)
    
    # Write the updated data to a new JSON file
    generate_json_file(updated_data, output_file_path)

    print(f"\n{output_file_name} schema updated with '{termset}' termset fields!\n")

def validate_argument(argument, valid_arguments, error):
    '''
    This function checks if the given argument is valid or not.

    Parameters:
    argument (str): The argument to validate.
    valid_arguments (list): A list of valid arguments.

    Returns:
    An error message and exits the program if the argument is not valid.
    '''

    if argument not in valid_arguments:
        print(f'Error: {error}')
        sys.exit(1)

    return argument in valid_arguments

# Helpers: Excel
def format_and_protect_worksheet(element):
    '''
    This function applies formatting and protection to the given worksheet.
    
    Parameters:
    worksheet: The worksheet to format.
    column_names: List of column names for determining the last column.
    locked_format: The format to lock the cells.
    merge_format: The format for merged cells.
    '''
    worksheet = element['worksheet']
    column_names = element['column_names']
    required_columns = element['required_columns']
    col_desc_eg = element['col_desc_eg']
    locked_format = element['locked_format']
    unlocked_format = element['unlocked_format']
    merge_format = element['merge_format']
    required_format = element['required_format']
    desc_eg_format = element['desc_eg_format']

    # Get the lexicographical letter of the last column based on the index
    last_column_letter = get_column_letter(len(column_names))
    
    # Write header in row 1 (header) and apply formatting
    for col, column_name in enumerate(column_names):
        if column_name in required_columns:
            worksheet.write(0, col, column_name, required_format)  # Bold the required headers
        else:
            worksheet.write(0, col, f'{column_name} (optional)', locked_format)  # Add (optional) to non-required headers

    # Write column description on row 2 and example in row 3
    for col, column_name in enumerate(column_names):
        # Write description in row 2 (index 1 in 0-based index)
        worksheet.write(1, col, col_desc_eg[column_name]['description'], desc_eg_format)  # Row 2

        # Write example in row 3 (index 2 in 0-based index)
        worksheet.write(2, col, f'e.g. {col_desc_eg[column_name]["example"]}', desc_eg_format)  # Row 3

    # Merge and write instruction in row 4
    merge_row(worksheet, 4, last_column_letter, merge_format)

    # Set the conditional format for locking rows 1 to 4
    worksheet.conditional_format(f'A1:{last_column_letter}4', {'type': 'no_errors', 'format': locked_format})

    # Set all rows below row 4 to unlocked
    worksheet.set_column(f'A5:{last_column_letter}1005', None, unlocked_format)

    # Protect the worksheet
    worksheet.protect()

def autofit_all_sheets(writer):
    for sheet in writer.sheets.values():
        sheet.autofit()

def get_excel_data_validation_from_regex(regex, column_letter, standard):
    # Define a mapping from regex patterns to Excel custom validation formulas
    # NB: Data starts from row 5
    row_start = 5

    REGEX_TO_EXCEL_DATA_VALIDATION_MAPPING = {
        '^[a-zA-Z0-9]+$': f'AND(LEN({column_letter}{row_start})>0, {column_letter}{row_start}=TEXTJOIN("", TRUE, IF(ISNUMBER(FIND(MID({column_letter}{row_start}, ROW(INDIRECT("1:"&LEN({column_letter}{row_start}))), 1), "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")), MID({column_letter}{row_start}, ROW(INDIRECT("1:"&LEN({column_letter}{row_start}))), 1), "")))',
        '^[a-zA-Z]+$': f'AND(LEN({column_letter}{row_start})>0, EXACT({column_letter}{row_start}, LOWER({column_letter}{row_start})), {column_letter}{row_start}=SUBSTITUTE({column_letter}{row_start}, " ", ""))',
        '^[0-9]{4}-[0-9]{{row_start}}-[0-9]{{row_start}}$': f'AND(LEN({column_letter}{row_start})>0, {column_letter}{row_start}=SUBSTITUTE(SUBSTITUTE({column_letter}{row_start}, "-", ""), " ", ""), ISNUMBER(SUBSTITUTE({column_letter}{row_start}, "-", "") + 0))',
        '^[-+]?([1-8]?\\d(\\.\\d+)?|90(\\.0+)?)$': f'AND(LEN({column_letter}{row_start})>0, {column_letter}{row_start}=SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE({column_letter}{row_start}, "-", ""), "+", ""), ".", ""), " ", ""), ISNUMBER(SUBSTITUTE(SUBSTITUTE(SUBSTITUTE({column_letter}{row_start}, "-", ""), "+", ""), ".", "") + 0))',
        '^[\\w-\\.]+@([\\w-]+\\.)+[\\w-]{2,4}$': f'AND(ISNUMBER(FIND("@", {column_letter}{row_start})), FIND(".", {column_letter}{row_start}, FIND("@", {column_letter}{row_start})) > FIND("@", {column_letter}{row_start}))'
    }

    # Return the corresponding Excel formula or None if regex is not in the mapping
    return REGEX_TO_EXCEL_DATA_VALIDATION_MAPPING.get(regex, None)

def apply_dropdown_list(component, dataframe, column_validation, pandas_writer, standard):
    sheet_name = convertStringToTitleCase(component['component'])
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
        print(f'Component "{component["component"]}" has duplicate column names found: ', dataframe.columns[dataframe.columns.duplicated()])
        # Remove duplicates
        dataframe = dataframe.loc[:, ~dataframe.columns.duplicated()]
    
    for column_name in dataframe.columns:
        if column_name in column_validation:
            is_field_required = column_validation[column_name].get('required', False)
            dropdown_list = column_validation[column_name].get('allowed_values', [])
            error_message = column_validation[column_name].get('error', f'{column_validation[column_name]["mapping"][standard]["label"]} required')
            field_type = column_validation[column_name].get('type', '')
            regex = column_validation[column_name].get('regex', '')

            # Get MS Excel official column header letter
            # Indexing starts at 0 by default but in this case, it should start at 1 so increment by 1
            column_index = dataframe.columns.get_loc(column_name)

            column_letter = get_column_letter(column_index + 1)

            # Get first row to the last row in a column
            # NB: The first 4 rows of the sheet are locked so the data starts from row 5
            row_start = 5 # Start from row 5
            row_end = 1005 # End at row 1005
            row_start_end = f'{column_letter}{row_start}:{column_letter}{row_end}'
            
            # Apply data formula to the column if regex is provided
            if regex:
                validation_formula = get_excel_data_validation_from_regex(regex, column_letter, standard)
                if validation_formula:
                    sheet.data_validation(row_start_end, {'validate': 'custom', 'value': validation_formula, 'input_message': 'Invalid input', 'error_message': error_message})

            # Apply the dropdown list to the column
            if dropdown_list:
                dropdown_list = list(set(dropdown_list)) # Remove duplicates

                # Capitalise the first letter of each word in the list and replace underscores with spaces
                dropdown_list = [i.title().replace('_', ' ') for i in dropdown_list]
                dropdown_list.sort() # Sort the list in ascending order
                number_of_characters = len(','.join(dropdown_list)) # Calculate the total length of the string

                if number_of_characters >= 255:
                    print(f'Info: "{column_name}" column dropdown too long for Excel. A hidden sheet will be created.')

                    # Start from row 5, leave row 1 for header, row 2 for file description, and row 3 for example data
                    for index, val in enumerate(dropdown_list, start=row_start):  
                        hidden_sheet.write(f'{column_letter}{index}', val)

                    # Create a range reference for the hidden sheet
                    data_validation_range = f'={hidden_sheet_name}!${column_letter}${row_start}:${column_letter}${index}'
                    sheet.data_validation(row_start_end, {'validate': 'list', 'source': data_validation_range, 'input_message': 'Choose from the list'})
                else:
                    sheet.data_validation(row_start_end, {'validate': 'list', 'source': dropdown_list, 'input_message': 'Choose from the list'})