from convert import extract_components_to_xlsx, extract_components_to_json, extract_components_to_xml, extract_components_to_html
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
    spreadsheet base schema to XLSX, JSON, HTML and XML formats.
    '''
    @classmethod
    def setUpClass(cls):
        '''Runs once before all test methods.'''
        print('\nSetting up test class...')
        cls.output_directory = 'test/outputs'
        cls.output_file_paths = []
        
        # Check if the output directory exists; if not, create it
        if not os.path.exists(cls.output_directory):
            os.makedirs(cls.output_directory)
        else:
            # Clean up output directory before running tests
            shutil.rmtree(cls.output_directory)
            
        # Check if schema base input file is valid and retrieve checklists
        helpers.validate_schema_file()
        helpers.get_checklists_from_xlsx_file()
        
    def setUp(self) -> None:
        print('\nSetting up test cases...')
        # Define the input JSON paths for testing
        self.base_file_path = helpers.SCHEMA_FILE_PATH
        self.standard = 'dwc' # options: 'mixs', 'tol', 'faang', 'dwc'
        self.schemas_directory = helpers.SCHEMA_BASE_DIR_PATH
        self.technology_name = 'sc_rnaseq' # options: 'stx_seq', 'stx_fish', 'sc_rnaseq'
        self.technology_label = 'Single-cell RNA Sequencing' # options: 'Spatial Transcriptomics', 'Single-cell RNA Sequencing'
        
    def tearDown(self) -> None:
        # Clean up output directory after tests
        print('\nCleaning up...')
        # if os.path.exists(self.output_directory):
        #     shutil.rmtree(self.output_directory)

    def run_extraction_test(self, format_type, extract_function):
        '''Generic function to test extraction for a given format.'''
        print(f'\nRunning test cases: Extract to {format_type}...')
        data_df, allowed_values_dict = helpers.read_xlsx_data()
        
        for checklist in helpers.CHECKLISTS_DICT.values():
            if self.standard and self.standard != checklist['standard_name']:
                continue
            
            if self.technology_name and self.technology_name != checklist['technology_name']:
                continue
                        
            element = {
                'allowed_values_dict': allowed_values_dict,
                'data_df': data_df,
                'version_column_name': checklist['version_column_name'],
                'version_column_label': checklist['version_column_label'],
                'version_description': checklist['version_description'],
                'standard_name': checklist['standard_name'],
                'standard_label': checklist['standard_label'],
                'technology_name': checklist['technology_name'],
                'technology_label': checklist['technology_label'],
                'file_path': helpers.SCHEMA_FILE_PATH,
                'output_file_name': checklist['output_file_name'],
                'output_file_path': os.path.join(self.output_directory, f"{checklist['output_file_name']}.{format_type}"),
            }
            
            self.output_file_paths.append(element['output_file_path'])

            element['data_df'] = helpers.filter_data_frame(element)
            
            if element['data_df'].empty:
                print(f"No data found for '{element['standard_name']}' standard and '{element['technology_name']}' technology. Skipping...")
                continue
            
            print(f"\n*-Generating '{element['standard_name']}' standard and '{element['technology_name']}' technology file-*")
            extract_function(element)

        # Check if file was created
        for output_file_path in list(set(self.output_file_paths)):
            self.assertTrue(os.path.exists(output_file_path), f'File not found: {output_file_path} with format: {format_type.upper()}')

            # Format-specific verification
            if format_type == 'xlsx' and output_file_path.endswith('.xlsx'):
                self.assertGreater(os.path.getsize(output_file_path), 0, f'File is empty: {output_file_path}')
            elif format_type == 'json' and output_file_path.endswith('.json'):
                with open(output_file_path, 'r') as json_file:
                    json_data = json.load(json_file)
                    self.assertTrue(any('component_name' in entry for entry in json_data), "'component_name' not found in any entry")

    def test_extract_to_xlsx(self):
        self.run_extraction_test('xlsx', extract_components_to_xlsx)

    def test_extract_to_json(self):
        self.run_extraction_test('json', extract_components_to_json)

    def test_extract_to_xml(self):
        self.run_extraction_test('xml', extract_components_to_xml)
        
    def test_extract_to_html(self):
        self.run_extraction_test('html', extract_components_to_html)
        
if __name__ == '__main__':
    unittest.main()