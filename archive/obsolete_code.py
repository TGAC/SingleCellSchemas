import pandas as pd
import json
import sys

def create_field(line):
    return {line['term_localName']: {'reference': line['iri'], 'required': False, 'type': 'string'}}
    
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