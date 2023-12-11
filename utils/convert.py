import pandas as pd
import sys
import json
def json_to_excel(json_path, excel_path):
    # Replace 'your_json_file.json' with the path to your JSON file or provide the JSON data directly
    with open(json_path, 'r') as json_file:
        data = pd.read_json(json_file)

    # Assuming 'sections' is a key in your JSON representing different sections
    sections = data['components']

    # Create a separate DataFrame for each section and transpose it
    section_dfs = [pd.json_normalize(section) for section in sections]

    # Replace 'output_file.xlsx' with the desired output Excel file name
    with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
        for i, section_df in enumerate(section_dfs, start=0):
            sheet_name = str(section_df.loc[0, "component"])
            if sheet_name == 'isolation':
                sheet_name = 'isolation_' + str(section_df['isolation_type.value'][0])
            section_df.to_excel(writer, sheet_name=sheet_name, header=False)


def extract_components_to_excel(json_data, output_file):

    with open(json_data, 'r') as json_file:
        json_data = json_file.read()
    # Load JSON data
    data_dict = json.loads(json_data)

    # Iterate through each component and create a DataFrame
    for component in data_dict.get('components', []):
        component_name = component.get('component')
        component_data = {}

        # Extract fields within the component
        for key, value in component.items():
            if key != 'component':
                component_data[key] = key

        # Create a DataFrame for the component
        df = pd.DataFrame([component_data])

        # Write the DataFrame to an Excel sheet named after the component
        with pd.ExcelWriter(output_file, engine='openpyxl', mode='a+') as writer:
            df.to_excel(writer, sheet_name=component_name, index=False)


if  __name__ == '__main__':
    args = sys.argv
    extract_components_to_excel(args[1], args[2])
    