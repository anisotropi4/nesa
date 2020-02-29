# nesa

This project consists of a series of scripts that extract data from the Network Rail National Electronic Sectional Appendix (NESA) into an, arguably, more useable format through Optical Character Recognition (OCR) and native PDF text extraction. 

The downloadable NESA data is available [here](https://www.networkrail.co.uk/industry-and-commercial/information-for-operators/national-electronic-sectional-appendix/) and contains as a set of route PDF files with spreadsheet and embedded TIFF image iles 

## Download the PDF files

The downloadable data for the **Anglia**,  **Kent, Sussex and Wessex**, **London North Eastern**, **London North Western (North)**, **London North Western (South)**, **Scotland** and **Western and Wales** routes are available [here](https://www.networkrail.co.uk/industry-and-commercial/information-for-operators/national-electronic-sectional-appendix/) 

However, as it is not possible to provide URLs to these files as cloud storage used to host these files precludes this, the first step is to manually download these seven route PDF files and place copies in the ```download``` directory

## Prerequisites
  * [jq](https://stedolan.github.io/jq) is a lightweight and flexible command-line JSON processor
  * [tabula](https://tabula.technology/) helps you liberate data tables trapped inside PDF files...
  * [poppler-utils](http://poppler.freedesktop.org/) package to extract and render PDF based on the xpdf-3.0 code base. 
  * [tesseract](https://tesseract-ocr.github.io/) is an open source text recognition (OCR) Engine, available under the Apache 2.0 license

## Execute the ```run.sh```

This runs a series of scripts to segment, extract and output the data
