from convert import extract_components_to_excel, extract_components_to_json, extract_components_to_xml
from utils import helpers

import json
import os
import pandas as pd
import re
import shutil
import unittest

class TestConvert(unittest.TestCase):
    '''
    A test case class for testing the conversion of 
    Excel schema to Excel, JSON, HTML and XML formats.
    '''

    def setUp(self) -> None:
        print('\nSetting up test cases...')
        # Define the input JSON paths for testing
        self.input_excel_files = helpers.SCHEMA_FILE_PATHS
        self.termset = 'core'
        self.namespace = 'dwc'
        self.schemas_directory = helpers.SCHEMA_BASE_DIR_PATH_XLSX
        self.output_directory = 'test/outputs'

        # Check if the output directory exists; if not, create it
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)

    def tearDown(self) -> None:
        # Clean up output directory after tests
        print('\nCleaning up...')
        # if os.path.exists(self.output_directory):
        #     shutil.rmtree(self.output_directory)

    def test_extract_to_excel(self):
        '''Test extraction and conversion to Excel format.'''
        print('\nRunning test cases: Extract to Excel...')

        for file_path in self.input_excel_files:
            if not file_path.endswith(helpers.DEFAULT_SCHEMA_EXTENSION):
                print(f'Unsupported file type: {file_path}')
                continue
            
            file_name = os.path.basename(file_path).replace(helpers.DEFAULT_SCHEMA_EXTENSION, f'_{self.namespace}_{self.termset}.xlsx')
            output_file_path = os.path.join(self.output_directory, file_name)
            data_df, allowed_values_dict = helpers.read_excel_data(file_path, self.namespace, self.termset)
            
            element = {
                'data_df': data_df,
                'allowed_values_dict': allowed_values_dict,
                'output_file_path': output_file_path,
                'termset': self.termset,
                'namespace': self.namespace
            }
            
            extract_components_to_excel(element)
            
            # Check if Excel file was created
            self.assertTrue(os.path.exists(output_file_path), f'Excel file not created for {file_path}')
            
            # Verify Excel content (e.g., checking sheet names or data structure)
            excel_data = pd.read_excel(output_file_path, sheet_name=None)
            self.assertGreater(len(excel_data), 0, 'Excel file is empty')

    def test_extract_to_json(self):
        '''Test extraction and conversion to JSON format.'''
        print('\nRunning test cases: Extract to JSON...')

        for file_path in self.input_excel_files:
            if not file_path.endswith(helpers.DEFAULT_SCHEMA_EXTENSION):
                print(f'Unsupported file type: {file_path}')
                continue
            
            file_name = os.path.basename(file_path).replace(helpers.DEFAULT_SCHEMA_EXTENSION, f'_{self.namespace}_{self.termset}.json')
            output_file_path = os.path.join(self.output_directory, file_name)
            data_df, allowed_values_dict = helpers.read_excel_data(file_path, self.namespace, self.termset)
            
            element = {
                'data_df': data_df,
                'allowed_values_dict': allowed_values_dict,
                'output_file_path': output_file_path,
                'termset': self.termset,
                'namespace': self.namespace
            }
            
            extract_components_to_json(element)
            
            # Check if JSON file was created
            self.assertTrue(os.path.exists(output_file_path), f'JSON file not created for {file_path}')
            
            # Verify JSON content structure
            with open(output_file_path, 'r') as json_file:
                json_data = json.load(json_file)
                # Check if 'component_name' exists in any dictionary within the list
                self.assertTrue(any('component_name' in entry for entry in json_data), "'component_name' not found in any entry")

    def test_extract_to_xml(self):
        '''Test extraction and conversion to XML format.'''
        print('\nRunning test cases: Extract to XML...')

        for file_path in self.input_excel_files:
            if not file_path.endswith(helpers.DEFAULT_SCHEMA_EXTENSION):
                print(f'Unsupported file type: {file_path}')
                continue
            
            file_name = os.path.basename(file_path).replace(helpers.DEFAULT_SCHEMA_EXTENSION, f'_{self.namespace}_{self.termset}.xml')
            output_file_path = os.path.join(self.output_directory, file_name)
            data_df, allowed_values_dict = helpers.read_excel_data(file_path, self.namespace, self.termset)
            
            element = {
                'data_df': data_df,
                'allowed_values_dict': allowed_values_dict,
                'output_file_path': output_file_path,
                'termset': self.termset,
                'namespace': self.namespace
            }
            
            extract_components_to_xml(element)

            # Check if XML file was created
            self.assertTrue(os.path.exists(output_file_path), f'XML file not created for {file_path}')

    '''
     def test_excel_sheet_names(self):
     #    return True

        # Get the component names from the JSON
        with open(self.input_json, 'r') as json_file:
            json_data = json_file.read()
        data_dict = json.loads(json_data)
        component_names = [component['component'] for component in data_dict['components']]

        # Check if the Excel sheet names match the component names
        sheet_names = list(self.excel_data.keys())
        self.assertEqual(sheet_names, component_names, 'Excel sheet names do not match component names')
    '''

if __name__ == '__main__':
    unittest.main()