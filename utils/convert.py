from io import BytesIO
from openpyxl.utils import cell
import json
import os
import numpy as np
import pandas as pd
import sys
import xlsxwriter


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
    output_core = output_file.replace(".json", "_core.json").replace("schemas/", "dist/checklists/json")
    output_core_xlsx = output_file.replace(".json", "_core.xlsx").replace("schemas/", "dist/checklists/xlsx")
    with open(output_core, "w") as joint_json:
        joint_json.write(json.dumps(data_dict))
   
    bytesIO = BytesIO()

    with pd.ExcelWriter(bytesIO, engine='xlsxwriter', mode='w+') as writer:
        for component in data_dict['components']:
            column_names = [get_heading(key) for key in component["fields"]]
            df = pd.DataFrame(columns=column_names)

            # Remove NaNs columns (if any rows are present)
            if not df.empty:
                df.dropna(axis=1, how='all', inplace=True)

            df.to_excel(writer, sheet_name=component['component'], index=False, header=True)

            # Get the column validation
            column_validation = get_validation(component)

            # Apply a dropdown list to the desired columns
            apply_dropdown_list(component, df, column_validation, writer)
          
        # Apply autofit to all sheets
        autofit_all_sheets(writer)

    # Reset the buffer position to the beginning
    bytesIO.seek(0)

    # Load the data from the buffer into a DataFrame
    df = pd.read_excel(bytesIO)

    # Save the DataFrame to an Excel file
    df.to_excel(output_core_xlsx, index=False)
     

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

def apply_dropdown_list(component, dataframe, column_validation, pandas_writer):
    sheet_name = component['component']
    fields = component['fields']
    field_validation = column_validation

    # cell = pandas_writer.book.add_format({'bold': True})
    print('Sheet name: ', sheet_name)
    # print('\nFields: ', fields)
    
    print("====================================\n")

    sheet = pandas_writer.sheets[sheet_name]
    workbook = pandas_writer.book

    # Create a hidden sheet for long dropdown lists
    hidden_sheet_name = 'HiddenDropdowns'
    if hidden_sheet_name not in workbook.sheetnames:
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
        # Ensure column_name exists
        if column_name not in dataframe.columns:
            raise ValueError(f"Column '{column_name}' does not exist in the DataFrame")
            continue

        if column_name in column_validation:
            is_field_required = column_validation[column_name].get('required', False)
            dropdown_list = column_validation[column_name].get('allowed_values', [])
            error_message = column_validation[column_name].get('error', '')
            field_type = column_validation[column_name].get('type', '')
            regex = column_validation[column_name].get('regex', '')

            print('Column name: ', column_name)

            # Get MS Excel official column header letter
            # Indexing starts at 0 by default but in this case, it should start at 1 so increment by 1
            column_index = dataframe.columns.get_loc(column_name)

            # Ensure column_index is a single integer
            if isinstance(column_index, np.ndarray):
                raise ValueError(f"Column '{column_name}' has duplicate entries in the DataFrame")

            column_letter = cell.get_column_letter(column_index + 1)

            # Get first row to the last row in a column 
            row_start_end = '%s2:%s1048576' % (column_letter, column_letter)
            
            # Apply data validation to the column if regex exists
            if regex:
                sheet.data_validation(row_start_end, {'validate': 'custom', 'value': regex})

            # Apply the dropdown list to the column
            if dropdown_list:
                dropdown_list = list(set(dropdown_list)) # Remove duplicates

                # Capitalise the first letter of each word in the list and replace underscores with spaces
                dropdown_list = [i.title().replace('_', ' ') for i in dropdown_list]
                dropdown_list.sort() # Sort the list in ascending order
                number_of_characters = sum(len(i) for i in dropdown_list)

                if number_of_characters >= 255:
                    # dataValidationColumn = '=%s!$%s$2:$%s$78'
                    print('The dropdown list is too long for Excel to handle. Please reduce the number of items in the list.')
                    col_letter = cell.get_column_letter(column_index + 1)

                    for index, val in enumerate(dropdown_list, start=2):  # Start from row 2 to leave row 1 for headers if needed
                        hidden_sheet.write(f'{col_letter}{index}', val)

                    # Create a range reference for the hidden sheet
                    data_validation_range = f'={hidden_sheet_name}!${col_letter}$2:${col_letter}${index}'
                    sheet.data_validation(row_start_end, {'validate': 'list', 'source': data_validation_range})
                else:
                    sheet.data_validation(row_start_end, {'validate': 'list', 'source': dropdown_list})


if __name__ == '__main__':
    args = sys.argv
    extract_components_to_excel(args[1], args[2], args[3])
    #get_dwc_fields()
