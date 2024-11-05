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
    JSON schema to Excel, JSON, and XML formats.
    '''

    def setUp(self) -> None:
        print('\nSetting up test cases...')
        # Define the input JSON paths for testing
        self.input_json_files = helpers.SCHEMA_FILE_PATHS
        self.termset = 'core'
        self.standard = 'dwc'
        self.schemas_directory = 'schemas/general'
        self.output_directory = 'test/outputs'

        # Check if the output directory exists; if not, create it
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)

    def tearDown(self) -> None:
        # Clean up output directory after tests
        print('\nCleaning up...')
        # if os.path.exists(self.output_directory):
        #     shutil.rmtree(self.output_directory)

    def get_schema_data(self, json_schema_file_path, termset, standard):
        # Get fields based on the termset
        termset_fields = helpers.retrieve_data_by_termset(termset)

        # Update schema data with termset fields
        helpers.update_schema_with_termset_fields(json_schema_file_path, termset_fields, termset)
        
        # Read JSON schema data
        with open(json_schema_file_path, 'r') as schema_data:
            data_dict = json.loads(schema_data.read())

        # Add the termset fields to the schema for the 'sample' component
        sample = next(d for d in data_dict['components'] if d['component'] == 'sample')

        # Extend the 'sample' component fields with DwC fields and remove duplicates
        sample['fields'] = helpers.remove_duplicates(sample['fields'], termset_fields)

        return data_dict

    def test_extract_to_excel(self):
        '''Test extraction and conversion to Excel format.'''
        print('\nRunning test cases: Extract to Excel...')

        for file_path in self.input_json_files:
            output_excel = re.sub(r'\.json$', f'_{self.standard}_{self.termset}.xlsx', file_path)
            output_excel = re.sub(self.schemas_directory, self.output_directory, output_excel) # Change output path
            data = self.get_schema_data(file_path, self.termset, self.standard)
            extract_components_to_excel(data, output_excel, self.termset, self.standard)
            
            # Check if Excel file was created
            self.assertTrue(os.path.exists(output_excel), f'Excel file not created for {file_path}')
            
            # Verify Excel content (e.g., checking sheet names or data structure)
            excel_data = pd.read_excel(output_excel, sheet_name=None)
            self.assertGreater(len(excel_data), 0, 'Excel file is empty')

    def test_extract_to_json(self):
        '''Test extraction and conversion to JSON format.'''
        print('\nRunning test cases: Extract to JSON...')

        for file_path in self.input_json_files:
            output_json = re.sub(r'\.json$', f'_{self.standard}_{self.termset}.json', file_path)
            output_json = re.sub(self.schemas_directory, self.output_directory, output_json) # Change output path
            data = self.get_schema_data(file_path, self.termset, self.standard)
            extract_components_to_json(data, output_json, self.termset, self.standard)

            # Check if JSON file was created
            self.assertTrue(os.path.exists(output_json), f'JSON file not created for {file_path}')
            
            # Verify JSON content structure
            with open(output_json, 'r') as json_file:
                json_data = json.load(json_file)
                self.assertIn('components', json_data, "JSON structure is missing 'components'")

    def test_extract_to_xml(self):
        '''Test extraction and conversion to XML format.'''
        print('\nRunning test cases: Extract to XML...')

        for file_path in self.input_json_files:
            output_xml = re.sub(r'\.json$', f'_{self.standard}_{self.termset}.xml', file_path)
            output_xml = re.sub(self.schemas_directory, self.output_directory, output_xml) # Change output path
            data = self.get_schema_data(file_path, self.termset, self.standard)
            extract_components_to_xml(data, output_xml, self.termset, self.standard)

            # Check if XML file was created
            self.assertTrue(os.path.exists(output_xml), f'XML file not created for {file_path}')

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