from openpyxl.utils import get_column_letter

import json
import os
import pandas as pd
import sys

# Helpers: General
ADDTL_FIELD_PROPERTIES = {
    'country': {
        'allowed_values':[],
        'description': 'The country where the sample was collected.',
        'error': 'Invalid country. Please enter a valid country.',
        'example': 'United Kingdom', 
        'regex': '^[A-Za-z ]+$',
        'required': False, 
        'show_in_output': True,
        'standards': {
            'dwc': {'label': '', 'name': ''},
            'mixs': {'label': '', 'name': ''},
            'schemaorg': { 'label': 'Country',  'name': 'country'}
        }
    },
    'day': {
        'description': 'The day of the month when the sample was collected.',
        'error': 'Invalid day. Please enter a valid day (01-31).',
        'example': '15', 
        'regex': '^(0[1-9]|[12][0-9]|3[01])$',
        'required': False, 
        'show_in_output': True,
        'standards': {
            'dwc': {'label': '', 'name': ''},
            'mixs': {'label': 'Weekday', 'name': 'weekday'},
            'schemaorg': { 'label': 'Day',  'name': 'day'},
        }
    },
    'decimalLatitude': {
        'description': 'The latitude of the sample collection site, in decimal degrees.',
        'error': 'Invalid decimal latitude. Please enter a valid decimal latitude.',
        'example': '52.2053', 
        'regex': '^-?([1-8]?\d(\.\d+)?|90(\.0+)?)$',
        'required': False, 
        'show_in_output': True,
        'standards': {
            'dwc': {'label': 'Decimal Latitude', 'name': 'decimalLatitude'},
            'mixs': {'label': 'Decimal Latitude', 'name': 'lat_lon'},
            'schemaorg': { 'label': 'Decimal Latitude',  'name': 'decimalLatitude'},
        },
        'unit': 'DD'
    },
    'decimalLongitude': {
        'description': 'The longitude of the sample collection site, in decimal degrees.',
        'error': 'Invalid decimal longitude. Please enter a valid decimal longitude.',
        'example': '0.1218', 
        'regex': '^-?(180(\.0+)?|((1[0-7]\d)|(\d{1,2}))(\.\d+)?)$',
        'required': False, 
        'show_in_output': True,
        'standards': {
            'dwc': {'label': 'Decimal Longitude', 'name': 'decimalLongitude'},
            'mixs': {'label': 'Decimal Longitude', 'name': 'lat_lon'},
            'schemaorg': {'label': 'Decimal Longitude', 'name': 'decimalLongitude'},
        },
        'unit': 'DD'
    },
    'family': {
        'description': 'The taxonomic family of the organism.',
        'error': 'Invalid family. Please enter a valid family',
        'example': 'Arenicolidae', 
        'regex': '^[A-Za-z]+$', 
        'required': False, 
        'show_in_output': True,
        'standards': {
            'dwc': {'label': 'Family', 'name': 'family'},
            'mixs': {'label': '', 'name': ''},
            'schemaorg': {'label': 'Family', 'name': 'family'},
        }
    },
    "genus": {
        "description": "The taxonomic genus of the organism.",
        "error": "Invalid genus. Please enter a valid genus",
        "example": "Arenicola",
        "regex": "^[A-Za-z]+$",
        "required": False,
        "show_in_output": True,
        "standards": {
        "dwc": {
            "label": "Genus",
            "name": "genus"
        },
        "mixs": {
            "label": "",
            "name": ""
        },
        "schemaorg": {
            "label": "Genus",
            "name": "genus"
        }
        }
    },
    "habitat": {
        "description": "The type of habitat where the sample was collected.",
        "error": "",
        "example": "Forest",
        "regex": "^[A-Za-z ]+$",
        "required": False,
        "show_in_output": True,
        "standards": {
        "dwc": {
            "label": "Location Remarks",
            "name": "locationRemarks"
        },
        "mixs": {
            "label": "Host Body Habitat",
            "name": "host_body_habitat"
        },
        "schemaorg": {
            "label": "Habitat",
            "name": "habitat"
        }
        }
    },
    "institutionCode": {
        "description": "The code or abbreviation representing the lead institution where the sample is held.",
        "error": "Name or acronym of institution is required",
        "example": "EI",
        "reference": "http://rs.tdwg.org/dwc/terms/institutionCode",
        "regex": "^[A-Z]{2,10}$",
        "required": False,
        "show_in_output": True,
        "standards": {
        "dwc": {
            "label": "",
            "name": ""
        },
        "mixs": {
            "label": "",
            "name": ""
        },
        "schemaorg": {
            "label": "Institution",
            "name": "institutionCode"
        }
        },
        "type": "string"
    },
    "lifeStage": {
        "allowed_values": [
        "Adult",
        "Egg",
        "Embryo",
        "Gametophyte",
        "Juvenile",
        "Larva",
        "Pupa",
        "Spore bearing structure",
        "Sporophyte",
        "Vegetative cell",
        "Vegetative structure",
        "Zygote",
        "Not applicable",
        "Not collected",
        "Not provided"
        ],
        "description": "The life stage of the organism when sampled.",
        "error": "Invalid life stage. Please enter a valid life stage (e.g., Adult).",
        "example": "Adult",
        "regex": "^[A-Za-z]+$",
        "required": False,
        "show_in_output": True,
        "standards": {
        "dwc": {
            "label": "Life Stage",
            "name": "lifeStage"
        },
        "mixs": {
            "label": "",
            "name": ""
        },
        "schemaorg": {
            "label": "Life Stage",
            "name": "lifeStage"
        }
        }
    },
    "materialEntityID": {
        "description": "A unique unique alphanumeric identifier for the material entity (sample).",
        "error": "Invalid material entity ID. Please enter a valid material entity ID (e.g., MAT-12345).",
        "example": "matEnt12345",
        "regex": "^[A-Z]{3}-\\d+$",
        "required": False,
        "show_in_output": True,
        "standards": {
        "dwc": {
            "label": "",
            "name": ""
        },
        "mixs": {
            "label": "",
            "name": ""
        },
        "schemaorg": {
            "label": "Material Entity ID",
            "name": "materialEntityID"
        }
        }
    },
    "materialSampleID": {
        "description": "A unique unique alphanumeric identifier for the material sample.",
        "error": "Invalid material sample ID. Please enter a valid material sample ID (e.g., MAT-12345).",
        "example": "matSample67890",
        "required": False,
        "regex": "^[A-Z]{4}-\\d+$",
        "show_in_output": True,
        "standards": {
        "dwc": {
            "label": "Material Sample ID",
            "name": "materialSampleID"
        },
        "mixs": {
            "label": "Source Material ID",
            "name": "source_mat_id"
        },
        "schemaorg": {
            "label": "Material Sample ID",
            "name": "materialSampleID"
        }
        }
    },
    "month": {
        "description": "The month when the sample was collected.",
        "error": "Invalid month. Please enter a valid month (01-12).",
        "example": "07",
        "regex": "^(0[1-9]|1[0-2])$",
        "required": False,
        "show_in_output": True,
        "standards": {
        "dwc": {
            "label": "",
            "name": ""
        },
        "mixs": {
            "label": "",
            "name": ""
        },
        "schemaorg": {
            "label": "Month",
            "name": "month"
        }
        }
    },
    "order": {
        "description": "The taxonomic order of the organism.",
        "example": "Capitellida",
        "regex": "^[A-Za-z]+$",
        "required": False,
        "show_in_output": True,
        "standards": {
        "dwc": {
            "label": "Order",
            "name": "order"
        },
        "mixs": {
            "label": "",
            "name": ""
        },
        "schemaorg": {
            "label": "Order",
            "name": "order"
        }
        }
    },
    "organismName": {
        "description": "The name of the organism.",
        "example": "Arenicola marina",
        "regex": "^[A-Za-z ]+$",
        "required": False,
        "show_in_output": True,
        "standards": {
        "dwc": {
            "label": "",
            "name": ""
        },
        "mixs": {
            "label": "",
            "name": ""
        },
        "schemaorg": {
            "label": "Organism Name",
            "name": "organismName"
        }
        }
    },
    "recordNumber": {
        "description": "A unique number assigned to this record.",
        "example": "rec123",
        "required": False,
        "show_in_output": True,
        "standards": {
        "dwc": {
            "label": "Record Number",
            "name": "recordNumber"
        },
        "mixs": {
            "label": "",
            "name": ""
        },
        "schemaorg": {
            "label": "Record Number",
            "name": "recordNumber"
        }
        }
    },
    'scientificName': {
        'description': 'The scientific name of the organism.', 
        'example': 'Arenicola marina', 
        'regex': '^[A-Za-z]+ [a-z]+$',
        'required': False, 
        'show_in_output': True,
        'standards': {
            'dwc': {'label': 'Scientific Name',  'name': 'scientificName'},
            'mixs': {'label': 'Specific Host Name',  'name': 'specific_host'},
            'schemaorg': {'label': 'Scientific Name',  'name': 'scientificName'},
        }
    },
    'sex': {
        'allowed_values': [
            'Asexual morph',
            'Female',
            'Hermaphrodite monoecious',
            'Male',
            'Sexual morph',
            'Not applicable',
            'Not collected',
            'Not provided'
        ],
        'error': 'Invalid value',
        'description': 'The sex of the organism (if applicable).', 
        'example': 'Male', 
        'regex': r'^(Asexual morph|Female|Hermaphrodite monoecious|Male|Sexual morph|Not applicable|Not collected|Not provided)$',
        'required': False, 
        'show_in_output': True,
        'standards': {
            'dwc': {'label':'Sex', 'name':'sex'},
            'mixs': {'label':'Urobiom Sex', 'name':'urobiom_sex'},
            'schemaorg': {'label':'Sex', 'name':'sex'}
        }
    },
    'taxonID': {
        'description': 'A unique identifier for species or organism studied.', 
        'error': 'Taxon ID is required',
        'example': '6344', 
        'reference': 'http://purl.obolibrary.org/obo/NCIT_C179773',
        'regex': '^\d+$',
        'required': True, 
        'show_in_output': True,
        'standards': {
            'dwc': {'label': 'Taxon ID', 'name': 'taxonID'},
            'mixs': {'label': 'Sample Taxon ID', 'name': 'samp_taxon_id'},
            'schemaorg': {'label': 'Taxon ID', 'name': 'taxonID'},
        }
    },
    'taxonRank': {
        'allowed_values':['Species', 'Subspecies'],
        'error': 'Invalid taxon rank. Please select a valid taxon rank.',
        'description': 'The rank of the taxon for this organism.', 
        'example': 'Species', 
        'regex': '^[A-Za-z]+$',
        'required': False, 
        'show_in_output': True,
        'standards': {
            'dwc': {'label': '', 'name': ''},
            'mixs': {'label': '', 'name': ''},
            'schemaorg': {'label': 'Taxon Rank',  'name': 'taxonRank'}
        },
    },
    'year': {
        'description': 'The year the sample was collected.', 
        'example': '2024', 
        'regex': '^\d{4}$',
        'required': False, 
        'show_in_output': True,
        'standards': {
            'dwc': {'label': '', 'name': ''},
            'mixs': {'label': '', 'name': ''},
            'schemaorg': {'label': 'Year',  'name': 'year'}
        }
    }
}

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

EXCLUDED_FILES = ['exclusions.json']

SCHEMA_FILE_PATHS = [f'schemas/{filename}' for root, dirs, files in os.walk('schemas/') 
                        for filename in files if filename.endswith('.json') and 
                        filename not in EXCLUDED_FILES
                    ]
STANDARDS = ['schemaorg', 'dwc', 'mixs']
TERMSETS = ['core', 'extended']

def convertStringToTitleCase(text):
    # Convert given a string to title case/sentence case
    return text.title().replace('_', ' ')

def create_field(line):
    return {line['term_localName']: {'reference': line['iri'], 'required': False, 'type': 'string'}}

def get_col_desc_eg(component, standard):
    field_validation = get_validation(component, standard)
    return {field: {'description': field_info.get('description', ''), 'example': field_info.get('example', '')} for field, field_info in field_validation.items()}

def get_dwc_fields(termset):
    '''
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
    '''
    # Read the CSV file
    orig = pd.read_csv('schemas/dwc.csv')

    # Load the JSON file
    with open('schemas/exclusions.json') as excluded_json:
        excluded = json.loads(excluded_json.read())['excluded']

    # Filter the data from the CSV file
    filtered = orig[(orig.status == 'recommended')]

    # Create the output list

    if termset == 'extended':
        out = [create_field(line) for _, line in filtered.iterrows()]
    elif termset == 'core':
        out = [create_field(line) for _, line in filtered.iterrows() if
               line['term_localName'] in [item['name'] for item in excluded if item['set'] == 'core']]
    else:
        sys.exit("Invalid termset. Please use 'core' or 'extended' as termset.")
    return out

def get_validation(component, standard):
    field_validation = {}

    for element in component['fields']:
        for field, field_info in element.items():
            if field_info.get('show_in_output', False):
                # Get the default label and name from the 'schemaorg' 
                # standard if no label or name is provided for the standard
                default_label = field_info.get('standards', {}).get('schemaorg', {}).get('label')
                default_name = field_info.get('standards', {}).get('schemaorg', {}).get('name')
                
                label = (
                    field_info.get('standards', {}).get(standard, {}).get('label') or 
                    default_label or  convertStringToTitleCase(field)
                )

                name = (
                    field_info.get('standards', {}).get(standard, {}).get('name') or
                    default_name or field
                )

                field_info.get('standards', dict())[standard]['label'] = label
                field_info['standards'][standard]['name'] = name
                field_validation[label] = field_info
    return field_validation

def get_field_label_mapping(component, standard):
    field_validation = get_validation(component, standard)
    label_mapping = {field: field_info.get('standards',dict()).get(standard,str()).get('name', field) for field, field_info in field_validation.items()}
    return label_mapping

def get_required_columns(component, standard):
    field_validation = get_validation(component, standard)
    return [field for field, field_info in field_validation.items() if field_info.get('required', False)]

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

def remove_duplicates(fields, new_fields):
   # Create a dictionary to hold unique fields by their key (e.g., 'sample_id')
    unique_fields = {}

    # Add existing fields to the unique_fields dictionary
    for field in fields:
        # Extract the key and the field data
        field_key = list(field.keys())[0]
        unique_fields[field_key] = field[field_key]

    # Add new fields (from new_fields), updating or adding as necessary
    for new_field in new_fields:
        new_field_key = list(new_field.keys())[0]
        unique_fields[new_field_key] = new_field[new_field_key]

    # Convert back to the original list of dictionaries format
    return [{key: value} for key, value in unique_fields.items()]

def set_field_properties(fields):
    required_fields = ['taxonID']
   
    for field in fields:
        for key, value in field.items():
            # Get field properties with default as an empty dictionary
            field_properties = ADDTL_FIELD_PROPERTIES.get(key, {})
            standards = field_properties.get('standards', dict())

            # Define default values and update with field properties if available
            value.update({
                'allowed_values': field_properties.get('allowed_values', []),
                'description': field_properties.get('description', ''),
                'error': field_properties.get('error', ''),
                'example': field_properties.get('example', ''),
                'regex': field_properties.get('regex', ''),
                'required': field_properties.get('required', key in required_fields),
                'show_in_output': field_properties.get('show_in_output', True if key in required_fields else False),
                'standards': {k: {'label': v.get('label', convertStringToTitleCase(k)), 'name': v.get('name', k)} for k, v in standards.items()}
            })
            
    return fields

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
            error_message = column_validation[column_name].get('error', f'{column_validation[column_name]["standards"][standard]["label"]} is required')
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