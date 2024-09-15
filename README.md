This repo contains developments regarding EI's CELLGEN ISP metadata standards. Broadly, the schemas can be used for describing a range of single cell genomic and spatial transcriptomics experiment types such as 10X and Vizgen. The schemas directory contains the JSON representation of the schema, and the utils directory contains python modules to convert from json to tabular formats such as excel.

To run the converter follow these steps:
- download or clone this repository and navigate to it in a terminal:
 ``cd SingleCellSchemas``
- create a new virtual environment called 'venv'
  ``python3 -m venv venv``
- activate the virtual environment
  - ``source venv/bin/activate``
- install dependencies
  ``pip install -r requirements/requirements.txt``
- Make 'dist' directory if it doesn't exist
  ``mkdir dist``
- run the converter
  ``python convert.py schemas/<datatype> dist/<output_name>.xlsx``
- **OR** run the tests (which also runs the converter whilst verifying the output)
  ``python -m unittest``
