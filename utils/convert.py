import pandas as pd
import sys
def json_to_excel(json_path, excel_path):
    # Replace 'your_json_file.json' with the path to your JSON file or provide the JSON data directly
    with open(json_path, 'r') as json_file:
        data = pd.read_json(json_file)

    # Assuming 'sections' is a key in your JSON representing different sections
    sections = data['components']

    # Create a separate DataFrame for each section and transpose it
    section_dfs = [pd.json_normalize(section).transpose() for section in sections]

    # Replace 'output_file.xlsx' with the desired output Excel file name
    with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
        for i, section_df in enumerate(section_dfs, start=1):
            sheet_name = str(section_df.loc["component", 0])
            if sheet_name == 'isolation':
                sheet_name = 'isolation_' + str(section_df.loc["component", 0])
            section_df.to_excel(writer, sheet_name=sheet_name, header=False)

if  __name__ == '__main__':
    args = sys.argv
    json_to_excel(args[1], args[2])
    