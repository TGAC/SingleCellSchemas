This repository contains developments regarding EI's CELLGEN ISP metadata standards.

Broadly, the schemas can be used for describing a range of single cell genomic and spatial transcriptomics experiment types such as 10X and Vizgen. The schemas directory contains the JSON representation of the schema, and the utils directory contains python modules to convert from json to tabular formats such as excel.

**Abbreviations**:

- SC RNASEQ: Single Cell RNA-Sequencing
- SPAT: Spatial Transcriptomics

<br />

Please follow the instructions below to convert the JSON schema to an excel file, xml and json files:

1. Download or clone this repository and navigate to its directory in the terminal

   `git clone https://github.com/TGAC/SingleCellSchemas.git`

   `cd SingleCellSchemas`

2. Create a new Python virtual environment called `venv`

   `python3 -m venv venv`

3. Activate the virtual environment

   `source venv/bin/activate`

4. Install dependencies

   `pip3 install -r requirements/requirements.txt`

5. Make the following directories if they do not exist

   `mkdir dist/checklists/json`

   `mkdir dist/checklists/xml`

   `mkdir dist/checklists/xlsx`

6. Different ways to run the `convert.py` script:

   - Use `launch.json` file to run the script in VSCode by selecting the appropriate configuration

      --**OR**--

   - `python3 convert.py <termset>`

      where `<termset>` is the type of terms to be used (extended, core)

      --**OR**--

   - `python3 convert.py schemas/<schema-name> <termset>`

      where `<schema-name>` is the name of the schema file in the `schemas` directory, `<termset>` is the type of terms to be used (extended, core)
      --**OR**--

   - `python3 convert.py schemas/<schema-name> <termset> <standard>`

      where `<schema-name>` is the name of the schema file in the `schemas` directory, `<termset>` is the type of terms to be used (extended, core) and `<standard>` is the standard to be used (e.g. dwc, mixs, schemaorg)

      --**OR**--

   - Run the tests (which also runs the converter whilst verifying the output)

      `python -m unittest`
