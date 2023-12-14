This repo contains developments regarding EI's CELLGEN ISP metadata standards. Broadly, the schemas can be used for describing a range of single cell genomic and spatial transcriptomics experiment types such as 10X, FACS and Vizgen. The schemas directory contains the JSON representation of the schema, and the utils directory contains python modules to convert from json to tabular formats such as excel.

To run the converter follow these steps:
- download this repository and navigate to it in a terminal
- create a new virtual environment
  - python3 -m venv venv
- activate it
  - source venv/bin/activate
- install dependencies
  - pip install -r requirements/requirements.txt
- run the converter
  - python convert.py schemas/single_cell_plant.json output/output.xlsx
- OR run the tests (which also runs the converter whilst verifying the output)
  - python -m unittest
