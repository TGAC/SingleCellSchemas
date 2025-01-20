'''
Script name: append_to_schema_data.py
Description:
    This script appends new data to the 'data' worksheet of an existing Excel schema file 
    while ensuring that the order of terms is maintained. The new data is appended based 
    on the 'component_name' and 'namespace_prefix' fields, ensuring seamless integration 
    with the existing schema structure.

Usage:
    $ python append_to_schema_data.py --file_path <path_to_existing_file> --new_data <path_to_new_data>

Parameters:
    - file_path (str): Path to the existing Excel schema file.
    - new_data (str): Path to the CSV Excel file containing new data to append.

Notes:
    - The script assumes the incoming data has the required schema fields.
    - The 'data' worksheet in the existing file is updated, preserving the term order.
'''

import pandas as pd
import utils.helpers as helpers
from openpyxl import load_workbook
import re

# Example namespace prefix mapping for validation
NAMESPACE_PREFIX_MAPPING = {
    'Schema1': 'Schema 1 Label',
    'Schema2': 'Schema 2 Label',
}

def append_data_to_spreadsheet(file_path, new_data):
    # Load the existing Excel file
    with pd.ExcelWriter(file_path, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
        # Read existing data from the 'data' worksheet
        existing_data = pd.read_excel(file_path, sheet_name='data', dtype=str)
        
        # Ensure new data columns match the existing data columns
        new_data = new_data.reindex(columns=existing_data.columns, fill_value='')
        
        # Concatenate the new data, maintaining the existing order
        combined_data = pd.concat([existing_data, new_data], ignore_index=True)
        
        # Sort the data by `component_name` and `namespace_prefix` to ensure proper order
        combined_data.sort_values(by=['component_name', 'namespace_prefix'], inplace=True)

        # Write the updated data back to the 'data' worksheet
        combined_data.to_excel(writer, sheet_name='data', index=False)
    
    print(f'New data appended successfully to {file_path} in the "data" worksheet!')

def validate_new_data(data_dict):
    '''
    Validates and processes the data dictionary based on given criteria.

    Parameters:
    - data_dict (dict): The data dictionary to validate.

    Returns:
    - pd.DataFrame: A validated DataFrame.
    '''
    # Convert the dictionary to a DataFrame for easier processing
    df = pd.DataFrame(data_dict)

    # Validation and corrections
    for index, row in df.iterrows():
        # Validate 'component_name'
        if not row['component_name']:
            raise ValueError(f'"component_name" cannot be empty. Row: {index}')

        # Validate or set 'component_label'
        if not row['component_label']:
            df.at[index, 'component_label'] = helpers.convertStringToTitleCase(row['component_name'])

        # Validate 'namespace_prefix'
        if not row['namespace_prefix']:
            raise ValueError(f'"namespace_prefix" cannot be empty. Row: {index}')

        # Validate 'term_name' and 'term_label'
        for col in ['term_name', 'term_label']:
            if not row[col]:
                raise ValueError(f'"{col}" cannot be empty. Row: {index}')

        # Validate 'term_required'
        if not isinstance(row['term_required'], bool):
            raise ValueError(f'"term_required" must be a boolean. Row: {index}')

        # Validate 'term_regex'
        if not row['term_regex'] or not row['term_regex'].startswith('^r'):
            raise ValueError(f'"term_regex" must be valid and start with '^r'. Row: {index}')

        # Set 'term_cardinality' if blank
        if not row['term_cardinality']:
            df.at[index, 'term_cardinality'] = 'single'

        # Set 'term_type' if blank
        if not row['term_type']:
            df.at[index, 'term_type'] = 'string'

        # Validate 'term_reference'
        if not re.match(r'https?://[^\s]+', row['term_reference']):
            raise ValueError(f'"term_reference" must be a valid URL. Row: {index}')

        # Validate 'termset'
        if row['termset'] not in helpers.TERMSETS:
            raise ValueError(f"'termset' must be 'core' or 'extended'. Row: {index}")

        # Validate 'schema_name'
        if not row['schema_name'] or row['schema_name'] not in NAMESPACE_PREFIX_MAPPING:
            raise ValueError(f"'schema_name' cannot be empty and must be in NAMESPACE_PREFIX_MAPPING. Row: {index}")

        # Set 'schema_label' if blank
        if not row['schema_label']:
            df.at[index, 'schema_label'] = NAMESPACE_PREFIX_MAPPING[row['schema_name']]

    return df

if __name__ == '__main__':
      # Path to the input Excel file containing sample data
    input_file = 'utils/input_data.xlsx'
    
    # Read new data from the Excel file
    new_data_df = pd.read_excel(input_file, sheet_name='data', dtype=str)
    
    # Validate and process the new data
    validated_data_df = validate_new_data(new_data_dict)
    
    # Schema file paths to append data to. It should begin with 'schemas/xlsx/' and end with '.xlsx'
    file_paths = [''] 
    
    for file_path in file_paths:
        # Extract the schema name from the file path (assuming schema name is in the file name)
        for schema_name in new_data_df['schema_name'].unique():
            if schema_name in file_path:
                # Filter the new data for the current schema
                filtered_data = new_data_df[new_data_df['schema_name'] == schema_name]

                # Call the function to append data
                append_data_to_spreadsheet(file_path, filtered_data)