import unittest
import pandas as pd
from utils.convert import extract_components_to_excel
import re

class TestConvert(unittest.TestCase):
    
    def test_json_to_excel(self):
        # Define the input JSON and output Excel file paths for testing
        input_json = "../schemas/single_cell_plant.json"
        output_excel = "../output/output.xlsx"
        
        # Call the json_to_excel function with the test data
        extract_components_to_excel(input_json, output_excel)

        
        # Read the generated Excel file
        excel_data = pd.read_excel(output_excel, sheet_name=None, header=None)
        
        # Assert that the Excel file contains the expected sheets and data
        self.assertIn("study", excel_data.keys())
        self.assertIn("sample", excel_data.keys())
        keys_set = set(excel_data.keys())
        # Assert that at least one key starts with isolation_
        regex_pattern = r'isolation_*'
        self.assertTrue(any(re.match(regex_pattern, key) for key in keys_set))

        # Assert that the data in study section sheet is correct
        #sample_data = excel_data["study"]
        #self.assertEqual(sample_data.iloc[0, 0], "component")
        #self.assertEqual(section1_data.iloc[1, 0], "value1")

        
if __name__ == '__main__':
    unittest.main()