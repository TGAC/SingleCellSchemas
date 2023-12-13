import pandas as pd
import sys
import json
import xlsxwriter

def extract_components_to_excel(json_data, output_file):
    with open(json_data, 'r') as json_file:
        json_data = json_file.read()
    # Load JSON data
    data_dict = json.loads(json_data)

    with pd.ExcelWriter(output_file, engine='xlsxwriter', mode='w+') as writer:
        # Iterate through each component and create a DataFrame
        components = data_dict['components']
        for component in components:
            component_name = component['component']
            # Extract the keys (column names) from the component
            #column_names = list(component["fields"].keys())[1:]  # Exclude 'component'
            column_names = []
            for key in list(component["fields"]):
                column_names.append(list(key.keys())[0])
            # Create a DataFrame with empty data
            df = pd.DataFrame(columns=column_names)
            # Write the DataFrame to an Excel sheet named after the component
            sheet_name = component_name
            df.to_excel(writer, sheet_name=sheet_name, index=False, header=True)
        for n, sheet in enumerate(writer.sheets):
            sheet = writer.sheets[sheet]
            sheet.autofit()

if __name__ == '__main__':
    args = sys.argv
    extract_components_to_excel(args[1], args[2])
