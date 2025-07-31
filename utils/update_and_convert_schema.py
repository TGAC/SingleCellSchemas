"""
Script Name: update_and_convert_schema.py
Description:
    This script converts the base schema into JSON and YAML formats.

Usage:
    python update_and_convert_schema.py --file_path <path_to_file> --output <output_path>
"""

import json
import os
import tempfile
import urllib.parse
import utils.helpers as helpers
import yaml


def generate_base_schema_yaml():
    """
    Generates a base schema YAML file by extracting schema information from an Excel file.
    The YAML file is stored in the schema base directory.
    """
    file_path = helpers.SCHEMA_FILE_PATH

    # Initialise base structure of the YAML schema
    combined_yaml_data = {
        "id": "https://w3id.org/linkml/examples/single_cell_model",
        "name": "singlecell_schema_model",
        "description": "The Single-cell schema YAML file contains metadata mapping and schemas related to the Earlham Institute's (EI's) CELLGEN ISP project. These metadata are designed to describe various Single Cell Genomics and Spatial Transcriptomics experiment types, including those from platforms like 10X Genomics and Vizgen.",
        "license": "https://creativecommons.org/publicdomain/zero/1.0/",
        "prefixes": {
            "dc": "http://purl.org/dc/elements/1.1",
            "dcterms": "http://purl.org/dc/terms/",
            "dwc": "http://rs.tdwg.org/dwc/terms/",
            "dwciri": "http://rs.tdwg.org/dwc/iri/",
            "linkml": "https://w3id.org/linkml/",
            "mixs": "https://w3id.org/mixs/",
            "schemaorg": "http://schema.org/",
            "singlecell": "https://singlecellschemas.org/terms/",
        },
        "default_curi_maps": ["semweb_context"],
        "imports": ["linkml:types"],
        "default_prefix": "singlecell",
        "default_range": "string",
        "classes": {},
        "enums": {},
    }

    # Read data once for all standards
    data_df, allowed_values_dict = helpers.read_xlsx_data()

    for checklist in helpers.CHECKLISTS_DICT.values():
        # Populate the element dictionary
        element = {
            "allowed_values_dict": allowed_values_dict,
            "data_df": data_df,
            "version_column_name": checklist["version_column_name"],
            "version_column_label": checklist["version_column_label"],
            "version_description": checklist["version_description"],
            "standard_name": checklist["standard_name"],
            "standard_label": checklist["standard_label"],
            "technology_name": checklist["technology_name"],
            "technology_label": checklist["technology_label"],
            "file_path": helpers.SCHEMA_FILE_PATH,
            "output_file_name": checklist["output_file_name"],
        }

        # Filter dataframe by namespace prefix name and schema name
        element["data_df"] = helpers.filter_data_frame(element)

        if element["data_df"].empty:
            print(
                f"No data found for '{element['standard_name']}' standard and '{element['technology_name']}' technology. Skipping..."
            )
            continue

        # Generate base YAML data for the filtered data
        yaml_data = helpers.get_base_schema_json(element)

        if yaml_data:
            version_column_name = element["version_column_name"]

            # Combine the YAML data for all standards
            for field in yaml_data:
                # if field.startswith('version_') and not field.get(version_column_name, ''):
                #     continue
                class_name = helpers.COMPONENTS.get(field.get("component_name", ""))
                if class_name not in combined_yaml_data["classes"]:
                    combined_yaml_data["classes"][class_name] = {"attributes": {}}

                is_multi_valued = (
                    False
                    if field.get("term_cardinality", "single") == "single"
                    else True
                )

                # Encode field names and labels to avoid special characters
                attribute_name = urllib.parse.quote(field.get("term_name", ""))
                attribute_label = urllib.parse.quote(field.get("term_label", ""))
                examples = (
                    [
                        {"value": example.strip()}
                        for example in str(field.get("term_example", "")).split(",")
                        if example.strip()
                    ]
                    if isinstance(field.get("term_example", ""), str)
                    else [{"value": str(field.get("term_example", ""))}]
                )

                combined_yaml_data["classes"][class_name]["attributes"][
                    attribute_name
                ] = {
                    "identifier": field.get("identifier", False),
                    "required": (
                        True if field.get(version_column_name, "") == "M" else False
                    ),
                    "description": field.get("term_description", ""),
                    "examples": examples,
                    "slot_uri": f"{field.get('namespace_prefix', '')}:{attribute_name}",
                    "domain": class_name,
                    "range": field.get("term_type", "string"),
                    "multivalued": is_multi_valued,
                    "inlined": False,
                }

                # Handle enums if available
                allowed_values = allowed_values_dict.get(attribute_name, "")
                if allowed_values and field.get("term_type", "string") == "enum":
                    enum_name = attribute_name.capitalize()
                    combined_yaml_data["enums"].setdefault(
                        enum_name, {"permissible_values": {}}
                    )
                    for value in allowed_values:
                        combined_yaml_data["enums"][enum_name]["permissible_values"][
                            value
                        ] = {}

    # Write YAML to a temporary file
    if combined_yaml_data["classes"]:
        with tempfile.NamedTemporaryFile(
            suffix=".yaml", delete=False, mode="w"
        ) as temp_file:
            temp_output_path = temp_file.name
            yaml.dump(
                combined_yaml_data,
                temp_file,
                sort_keys=False,
                default_flow_style=False,
                indent=2,
            )

        # Overwrite the original file with the generated YAML file
        file_name = os.path.basename(file_path).replace(".xlsx", ".yaml")
        output_file = f"{helpers.SCHEMA_DIR_PATH}/{file_name}"
        os.replace(temp_output_path, output_file)
        print(f"Base YAML file generated/updated: {output_file}")
    else:
        print("No data to generate YAML file.")


def generate_base_schema_json():
    """
    Generates a base schema JSON file by extracting schema information from an Excel file.
    The JSON file is stored in the schema base directory.
    """
    file_path = helpers.SCHEMA_FILE_PATH
    combined_json_data = []

    # Read data once for all standards
    data_df, allowed_values_dict = helpers.read_xlsx_data()

    for checklist in helpers.CHECKLISTS_DICT.values():
        # Populate the element dictionary
        element = {
            "allowed_values_dict": allowed_values_dict,
            "data_df": data_df,
            "version_column_name": checklist["version_column_name"],
            "version_column_label": checklist["version_column_label"],
            "version_description": checklist["version_description"],
            "standard_name": checklist["standard_name"],
            "standard_label": checklist["standard_label"],
            "technology_name": checklist["technology_name"],
            "technology_label": checklist["technology_label"],
            "file_path": helpers.SCHEMA_FILE_PATH,
            "output_file_name": checklist["output_file_name"],
        }

        # Filter dataframe by namespace prefix name and schema name
        element["data_df"] = helpers.filter_data_frame(element)

        if element["data_df"].empty:
            print(
                f"No data found for '{element['standard_name']}' standard and '{element['technology_name']}' technology. Skipping..."
            )
            continue

        # Generate base JSON data for the filtered data
        json_data = helpers.get_base_schema_json(element)

        if json_data:  # Only extend if json_data is not empty
            # Add the modified json_data to the combined_json_data list
            combined_json_data.extend(json_data)
        else:
            print(
                f"No valid json_data for schema: {element['technology_name']}, namespace: {element['standard_name']}, skipping."
            )

    # Write JSON to a temporary file
    if combined_json_data:
        with tempfile.NamedTemporaryFile(
            suffix=".json", delete=False, mode="w"
        ) as temp_file:
            temp_output_path = temp_file.name
            json.dump(
                combined_json_data,
                temp_file,
                indent=4,
                default=helpers.datetime_converter,
            )

        # Overwrite the original file with the generated JSON file
        file_name = os.path.basename(file_path).replace(".xlsx", ".json")
        output_file = f"{helpers.SCHEMA_DIR_PATH}/{file_name}"
        os.replace(temp_output_path, output_file)
        print(f"Base JSON file generated/updated: {output_file}")
    else:
        print("No data to generate JSON file.")


if __name__ == "__main__":
    # Check if schema base input file is valid
    is_schema_file_valid = helpers.validate_schema_file()

    # Generate base schema JSON and YAML files
    if is_schema_file_valid:
        # Get checklists from the schema file
        helpers.get_checklists_from_xlsx_file()

        # Delete existing matching schema files
        helpers.remove_existing_schema_files()

        generate_base_schema_json()
        print("\n_______\n")
        generate_base_schema_yaml()
