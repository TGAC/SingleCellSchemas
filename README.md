# SingleCellSchema

The **SingleCellSchema** repository houses developments related to Earlham Institute's (EI’s) CELLGEN ISP metadata mapping and schemas, designed to describe a variety of Single Cell Genomics and Spatial Transcriptomics experiment types, such as those from 10X Genomics and Vizgen.

Visit the SingleCellSchema website at https://singlecellschemas.org.

---

The **SingleCellSchema** repository contains the following directories:

- `dist`: contains the output files generated from the conversion process.

- `schemas`: contains the xlsx base versions of the schema.

- `utils`: contains Python helper scripts to convert the base XLSX file into formats such as HTML, XML and XLSX.

The `update_and_convert_schema.py` script is responsible for updating the XLSX base schema files located in the `schemas` directory and generating corresponding YAML and JSON files based on the XLSX file. The script is located in the `utils` directory.

The main script, `convert.py`, is used to convert the XLSX schema into XLSX, XML, html and JSON files according to the namespace prefix. It is found in the project root directory.

> **Important note**:
Please do not directly modify the base YAML and JSON files in the `schemas` directory. To make changes, update the `data` worksheet in `base_sc_schemas.xlsx` spreadsheet located in the `schemas` directory.

After making changes to the base XLSX file, run the `update_and_convert_schema.py` script in the `utils` directory to regenerate and update the YAML and JSON files. To run the update script, execute in the terminal - `python3 utils/update_and_convert_schema.py`.

**Abbreviations**:

- SC RNASEQ: Single Cell RNA-Sequencing
- STX: Spatial Transcriptomics

<br />

Please follow the instructions below to convert the XLSX schema into an xlsx, xml, html and json files:

1. Download or clone this repository and navigate to its directory in the terminal

   `git clone https://github.com/TGAC/SingleCellSchemas.git`

   `cd SingleCellSchemas`

2. Create a new Python virtual environment called `venv`

   `python3 -m venv venv`

3. Activate the virtual environment

   `source venv/bin/activate`

4. Install dependencies

   `pip3 install -r requirements.txt`

5. Different ways to run the `convert.py` script which is found in the project root directory

   - Use `launch.xlsx` file to run the script in VSCode by selecting the appropriate configuration

     --**OR**--

   - `python3 convert.py`

     This will convert the schema into a spreadsheet file, xml and json files using
     all namespace prefixes and schemas in the `schemas` directory

     --**OR**--

   - `python3 convert.py <namespace_prefix>`

     where `<namespace_prefix>` is the namespace prefix to be used (e.g. dwc, faang, mixs, tol)
     e.g. `python3 convert.py dwc`

     --**OR**--

   - `python3 convert.py <format_type>`

     where `<format_type>` is the format type that the output will be returned in (e.g. xlsx, xml, html, json)
      e.g. `python3 convert.py html`

     --**OR**--

   - Run the tests (which also runs the converter whilst verifying the output)

     `python -m unittest`
