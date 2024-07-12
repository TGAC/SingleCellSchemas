import pandas as pd
import sys
import json
import xlsxwriter
import os

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
    output_core = output_file.replace(".json", "_core.json").replace("schemas/", "dist/")
    output_core_xlsx = output_file.replace(".json", "_core.xlsx").replace("schemas/", "dist/")
    with open(output_core, "w") as joint_json:
        joint_json.write(json.dumps(data_dict))

    with pd.ExcelWriter(output_core_xlsx, engine='xlsxwriter', mode='w+') as writer:
        for component in data_dict['components']:
            column_names = [get_heading(key) for key in component["fields"]]
            df = pd.DataFrame(columns=column_names)
            df.to_excel(writer, sheet_name=component['component'], index=False, header=True)
        autofit_all_sheets(writer)

def get_heading(key):
    fieldset = list(key.keys())[0]
    return key.get(fieldset, {}).get("label", fieldset)

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

if __name__ == '__main__':
    args = sys.argv
    extract_components_to_excel(args[1], args[2], args[3])
    #get_dwc_fields()
