import unittest, json
import pandas as pd
from utils.convert import extract_components_to_excel
import re

class TestConvert(unittest.TestCase):
    """
    A test case class for testing the conversion of JSON to Excel.
    """

    def setUp(self) -> None:
        # Define the input JSON and output Excel file paths for testing
        self.input_json = "schemas/single_cell_plant.json"
        self.output_excel = "dist/EICore.xlsx"
        # Call the json_to_excel function with the test data
        extract_components_to_excel(self.input_json, self.output_excel)
        # Read the generated Excel file
        self.excel_data = pd.read_excel(self.output_excel, sheet_name=None, header=None)

    def test_excel_sheet_names(self):
        # Get the component names from the JSON
        with open(self.input_json, 'r') as json_file:
            json_data = json_file.read()
        data_dict = json.loads(json_data)
        component_names = [component['component'] for component in data_dict['components']]

        # Check if the Excel sheet names match the component names
        sheet_names = list(self.excel_data.keys())
        self.assertEqual(sheet_names, component_names, "Excel sheet names do not match component names")

if __name__ == '__main__':
    unittest.main()