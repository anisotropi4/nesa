# nesa

This project consists of a series of scripts that extract data from the Network Rail National Electronic Sectional Appendix (NESA) into a series of Route Clearance reports using PDF text extraction. 

The downloadable NESA data is available [here](https://www.networkrail.co.uk/industry-and-commercial/information-for-operators/national-electronic-sectional-appendix/) and contains as a set of route PDF files with spreadsheet and embedded TIFF image iles 

## Extracted data download links

|Unformatted text|Per page Route Clearance TSV|Route Clearance XLSX Report|
|----------------|----------------------------|---------------------------|
|[Anglia Route](Anglia-Route/anglia-route-text.md)|[Anglia Route](Anglia-Route/anglia-route-tsv.md)|[Anglia Route](Anglia-Route/anglia-route-clearance.xlsx)|
|[Kent, Sussex and Wessex](Kent-Sussex-Wessex/kent-sussex-wessex-text.md)|[Kent, Sussex and Wessex](Kent-Sussex-Wessex/kent-sussex-wessex-tsv.md)|[Kent, Sussex and Wessex](Kent-Sussex-Wessex/kent-sussex-wessex-clearance.xlsx)|
|[London North-Eastern](London-North-Eastern/london-north-eastern-text.md)|[London North-Eastern](London-North-Eastern/london-north-eastern-tsv.md)|[London North-Eastern](London-North-Eastern/london-north-eastern-clearance.xlsx)|
|[London North-Western North](London-North-Western-North/london-north-western-north-text.md)|[London North-Western North](London-North-Western-North/london-north-western-north-tsv.md)|[London North-Western North](London-North-Western-North/london-north-western-north-clearance.xlsx)|
|[London North-Western South](London-North-Western-South/london-north-western-south-text.md)|[London North-Western South](London-North-Western-South/london-north-western-south-tsv.md)|[London North-Western South](London-North-Western-South/london-north-western-south-clearance.xlsx)|
|[Scotland](Scotland/scotland-text.md)|[Scotland](Scotland/scotland-tsv.md)|[Scotland](Scotland/scotland-clearance.xlsx)|
|[Western and Wales](Western-and-Wales/western-and-wales-text.md)|[Western and Wales](Western-and-Wales/western-and-wales-tsv.md)|[Western and Wales](Western-and-Wales/western-and-wales-clearance.xlsx)|

## Data Source
The PDF files for these seven routes are available [here](https://www.networkrail.co.uk/industry-and-commercial/information-for-operators/national-electronic-sectional-appendix/)

## Prerequisites
  * [jq](https://stedolan.github.io/jq) is a lightweight and flexible command-line JSON processor. On an [Debian](https://debian.org) or similar `apt` based Linux system:

   $ sudo apt install jq

  * [poppler-utils](http://poppler.freedesktop.org/) package to decompress, extract text and render PDF based on the xpdf-3.0 code base

   $ sudo apt install poppler-utils

  * [ghostscript](https://www.ghostscript.com/) package to interpret and manipulate PostScript and PDF files

   $ sudo apt install ghostscript

### `python` dependencies
  * [python 3.8](https://www.python.org/) to run the scripts PDF based on the xpdf-3.0 code base. Tested against Python 3.7 and 3.8
  * Python [pandas](https://pandas.pydata.org/) data processing library
  * Python [pdfplumber](https://github.com/jsvine/pdfplumber) table and visual debugging PDF data extract library 
  * Python [pdfminer.six](https://github.com/pdfminer/pdfminer.six) PDF information extraction library
  * Python [openpyxl](https://openpyxl.readthedocs.io/en/stable/) library to write `Excel 2010 xlsx` files

#### `python virtualenv` package
For ease of use manage `python` packages dependencies with a local virtual environment `venv` using the python `virtualenv` package:

    $ sudo apt install virtualenv
    $ virtualenv venv
    $ source venv/bin/activate
    $ pip install -r requirements.txt

## Creating the Route Clearance reports
The reports for the routes are created as follows:

### Download the data

Download the seven route Section Appendix PDF files into the ```download``` directory from [here](https://www.networkrail.co.uk/industry-and-commercial/information-for-operators/national-electronic-sectional-appendix/)

### Process the PDF files

To extract the data execute the ```run.sh``` script:

    $ ./run.sh

This executes a series of scripts to segment, extract and output the data creating a series of `TSV` and `Excel` spreadsheets in the seven route directories

## License

Network Rail are copyright holder and retain all intellectual property rights related to the data and derived data contained within the National Electronic Sectional Appendix as set out [here](https://www.networkrail.co.uk/terms-and-conditions/)

The scripts and other material is provided under the the terms set out in the LICENSE  

## Acknowledgement

The authors would like to thank Network Rail for providing this data and to all the contributors to the 
