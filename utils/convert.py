import pandas as pd
import sys
import json
import xlsxwriter

def extract_components_to_excel(json_data, output_file):
    with open(json_data, 'r') as json_file:
        json_data = json_file.read()
    # Load JSON data
    data_dict = json.loads(json_data)
    dwc = get_dwc_fields()
    sample = [d for d in data_dict["components"] if d["component"] == "sample"]
    sample[0]["fields"].extend(dwc)




    with pd.ExcelWriter(output_file, engine='xlsxwriter', mode='w+') as writer:
        # Iterate through each component and create a DataFrame
        components = data_dict['components']
        for component in components:
            component_name = component['component']
            # Extract the keys (column names) from the component
            #column_names = list(component["fields"].keys())[1:]  # Exclude 'component'
            column_names = []
            for key in list(component["fields"]):
                fieldset = list(key.keys())[0]
                try:
                    heading = key[fieldset]["label"]
                except KeyError:
                    heading = fieldset
                column_names.append(heading)
            # Create a DataFrame with empty data
            df = pd.DataFrame(columns=column_names)
            # Write the DataFrame to an Excel sheet named after the component
            sheet_name = component_name
            df.to_excel(writer, sheet_name=sheet_name, index=False, header=True)
        for n, sheet in enumerate(writer.sheets):
            sheet = writer.sheets[sheet]
            sheet.autofit()

def get_dwc_fields():
    orig = pd.read_csv("schemas/dwc.csv")
    with open("schemas/exclusions.json") as excluded_json:
        excluded = json.loads(excluded_json.read())["excluded"]
    out = list()
    filtered = orig[(orig.status == "recommended") | (orig.status == "required")]
    for idx, line in filtered.iterrows():
        for ex in excluded:
            if line["label"] == ex:
                pass
            else:
                out.append({line["term_localName"]: {"reference": line["iri"], "required": False, "type": "string"}})
    return out

if __name__ == '__main__':
    args = sys.argv
    extract_components_to_excel(args[1], args[2])
    #get_dwc_fields()
