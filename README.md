# SingleCellSchema

The **SingleCellSchema** repository houses developments related to Earlham Institute's (EI’s) CELLGEN ISP metadata mapping and schemas, designed to describe a variety of Single Cell Genomics and Spatial Transcriptomics experiment types, such as those from 10X Genomics and Vizgen.

It contains the following directories:

- `dist`: contains the output files generated from the conversion process.

- `schemas`: contains the core, extended and general versions of the schema in JSON format.

- `utils`: contains Python helper scripts to convert JSON files into tabular formats such as Excel.

The main script, `convert.py`, is used to convert the JSON schema into Excel, XML, and additional JSON files. It is found in the project root directory.

**Abbreviations**:

- SC RNASEQ: Single Cell RNA-Sequencing
- STX: Spatial Transcriptomics

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

   ### Core directories

   `mkdir dist/checklists/core/json`

   `mkdir dist/checklists/core/xml`

   `mkdir dist/checklists/core/xlsx`

   ### Extended directories

   `mkdir dist/checklists/extended/json`

   `mkdir dist/checklists/extended/xml`

   `mkdir dist/checklists/extended/xlsx`

6. Different ways to run the `convert.py` script which is found in the project root directory

   - Use `launch.json` file to run the script in VSCode by selecting the appropriate configuration

     --**OR**--

   - `python3 convert.py`

     This will convert the schema into an excel file, xml and json files using
     all termsets, standards and schemas in the `schemas/base` directory

     --**OR**--

   - `python3 convert.py <termset>`

     where `<termset>` is the type of terms to be used (extended, core)
     e.g. `python3 convert.py core`

     --**OR**--

   - `python3 convert.py schemas/base/<schema-name> <termset>`

     where `<schema-name>` is the name of the schema file in the `schemas` directory, `<termset>` is the type of terms to be used (extended, core) e.g. `python3 convert.py schemas/base/sc_rnaseq.json core`

     --**OR**--

   - `python3 convert.py schemas/base/<schema-name> <termset> <standard>`

     where `<schema-name>` is the name of the schema file in the `schemas` directory, `<termset>` is the type of terms to be used (extended, core) and `<standard>` is the standard to be used (e.g. dwc, mixs, schemaorg)
     e.g. `python3 convert.py schemas/base/sc_rnaseq.json core dwc`

     --**OR**--

   - Run the tests (which also runs the converter whilst verifying the output)

     `python -m unittest`
