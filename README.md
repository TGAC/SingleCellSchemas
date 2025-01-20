# SingleCellSchema

The **SingleCellSchema** repository houses developments related to Earlham Institute's (EI’s) CELLGEN ISP metadata mapping and schemas, designed to describe a variety of Single Cell Genomics and Spatial Transcriptomics experiment types, such as those from 10X Genomics and Vizgen.

Visit the SingleCellSchema website at https://singlecellschemas.org.

---

The **SingleCellSchema** repository contains the following directories:

- `dist`: contains the output files generated from the conversion process.

- `schemas/xlsx`: contains the xlsx base versions of the schema.

- `utils`: contains Python helper scripts to convert base Excel files into formats such as HTML, XML and Excel.

The `update_and_convert_schema.py` script is responsible for updating the Excel base schema files located in the `schemas/xlsx` directory and generating corresponding JSON files based on these Excel files. The script is located in the `utils` directory.

The main script, `convert.py`, is used to convert the Excel schema into Excel, XML, html and JSON files according to the namespace prefix. It is found in the project root directory.

> **Important note**:
Please do not directly modify the base JSON files in the `schemas/json directory`. To make changes, update the `data` worksheet in one of the base Excel files located in the `schemas/xlsx` directory.

After making changes to the Excel files, run the `update_and_convert_schema.py` script in the `utils` directory to regenerate and update the JSON schema files. To run the update script, execute in the terminal - `python3 utils/update_and_convert_schema.py`.

**Abbreviations**:

- SC RNASEQ: Single Cell RNA-Sequencing
- STX: Spatial Transcriptomics

<br />

Please follow the instructions below to convert the Excel schema into an excel file, xml, html and json files:

1. Download or clone this repository and navigate to its directory in the terminal

   `git clone https://github.com/TGAC/SingleCellSchemas.git`

   `cd SingleCellSchemas`

2. Create a new Python virtual environment called `venv`

   `python3 -m venv venv`

3. Activate the virtual environment

   `source venv/bin/activate`

4. Install dependencies

   `pip3 install -r requirements/requirements.txt`

5. Different ways to run the `convert.py` script which is found in the project root directory

   - Use `launch.xlsx` file to run the script in VSCode by selecting the appropriate configuration

     --**OR**--

   - `python3 convert.py`

     This will convert the schema into an excel file, xml and json files using
     all termsets, namespace prefixes and schemas in the `schemas/xlsx` directory

     --**OR**--

   - `python3 convert.py <termset>`

     where `<termset>` is the type of terms to be used (extended, core)
     e.g. `python3 convert.py core`

     --**OR**--

   - `python3 convert.py schemas/xlsx/<schema-file-path> <termset>`

     where `<schema-file-path>` is the name of the schema file in the `schemas/xlsx` directory, `<termset>` is the type of terms to be used (extended, core) e.g. `python3 convert.py schemas/xlsx/sc_rnaseq.xlsx core`

     --**OR**--

   - `python3 convert.py schemas/xlsx/<schema-file-path> <termset> <namespace_prefix>`

     where `<schema-file-path>` is the name of the schema file in the `schemas/xlsx` directory, `<termset>` is the type of terms to be used (extended, core) and `<namespace_prefix>` is the namespace prefix to be used (e.g. dwc, mixs, tol)
     e.g. `python3 convert.py schemas/xlsx/sc_rnaseq.xlsx core dwc`

     --**OR**--

   - Run the tests (which also runs the converter whilst verifying the output)

     `python -m unittest`
