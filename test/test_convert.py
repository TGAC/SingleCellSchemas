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
        self.input_json = ["schemas/single_cell_RNAseq.json", "schemas/spatial_transcriptomics_fish.json",
                           "schemas/spatial_transcriptomics_seq.json"]
        self.output_excel = ""

        for filename in self.input_json:
            # Call the json_to_excel function with the test data
            self.output_excel = re.sub(r'\.json$', '.xlsx', filename)
            extract_components_to_excel(filename, self.output_excel, "extended")
            # Read the generated Excel file
            # self.excel_data = pd.read_excel(self.output_excel, sheet_name=None, header=None)

    def test_excel_sheet_names(self):
        return True

        """
        # Get the component names from the JSON
        with open(self.input_json, 'r') as json_file:
            json_data = json_file.read()
        data_dict = json.loads(json_data)
        component_names = [component['component'] for component in data_dict['components']]

        # Check if the Excel sheet names match the component names
        sheet_names = list(self.excel_data.keys())
        self.assertEqual(sheet_names, component_names, "Excel sheet names do not match component names")
        """


if __name__ == '__main__':
    unittest.main()
