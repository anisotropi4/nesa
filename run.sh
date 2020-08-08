#!/bin/bash

IFS=$'\012'

source venv/bin/activate
export NESADIR=${PWD}
export PATH=${PATH}:${NESADIR}

if [ ! -s section-list.json ]; then
    for FILEPATH in $(ls download/*Sectional\ Appendix*.pdf)
    do
        FILENAME=$(basename ${FILEPATH})
        ROUTE=$(echo ${FILENAME} | sed 's/ Sectional Appendix .*.pdf//; s/[,)(]//g; s/ /-/g')
        echo "{"\"${ROUTE}\": \"${FILENAME}\""}"
    done | jq -cs '.' > section-list.json
fi

for ROUTE in $(jq -r '.[] | keys[]' section-list.json)
do
    echo Processing ${ROUTE}
    for i in pdf images tsv txt work stage output report
    do
        if [ ! -d ${ROUTE}/${i} ]; then
            mkdir -p ${ROUTE}/${i}
        fi
    done
    FILENAME=$(jq -r '.[] | select(. | keys[] == "'${ROUTE}'") | .[]' section-list.json)
    if [ -z "$(ls -A ${ROUTE}/pdf/)" ]; then
        echo Extract PDF pages
        (cd ${ROUTE}/pdf; pdfseparate "../../download/${FILENAME}" pg_%04d.pdf)
    fi
    for i in ${ROUTE}/pdf/*.pdf
    do
        echo ${i}
        FILESTUB=$(basename ${i} | sed 's/.pdf//')
        PDFPATH=${ROUTE}/work/${FILESTUB}.pdf
        if [ ! -f ${PDFPATH} ]; then
            N=$(pdfimages -list ${i} | wc -l)
            if [ ${N} = 2 ]; then
                gs -q -dSAFER -dEmbedAllFonts=true -dNOPAUSE -dBATCH -dPDFA=1 -dNOOUTERSAVE -sProcessColorModel=DeviceCMYK -sPDFACompatibilityPolicy=1 -sDEVICE=pdfwrite -sOutputFile=${PDFPATH} ${i}
                qpdf --replace-input --stream-data=uncompress ${PDFPATH}
                if [ ! -f output/${FILESTUB}.pdf ]; then
                    (cd ${ROUTE}; filter_pdf.py work/${FILESTUB}.pdf)
                fi
            fi
        fi
        TXTPATH=${ROUTE}/txt/${FILESTUB}.txt
        if [ ! -f ${TXTPATH} ]; then
            pdftotext -layout -nopgbrk ${i} ${TXTPATH}
        fi
    done
    if [ -z "$(ls -A ${ROUTE}/report/)" ]; then
        echo Extract text
        ./collate-gauge.py ${ROUTE}
    fi
 done

for ROUTE in $(jq -r '.[] | keys[]' section-list.json)
do
    echo ${ROUTE}
    FILENAME=$(jq -r '.[] | select(. | keys[] == "'${ROUTE}'") | .[]' section-list.json)
    if [ -z "$(ls -A ${ROUTE}/images/)" ]; then
        echo Create PNG images
        pdftoppm -r 300 -png "download/${FILENAME}" ${ROUTE}/images/pg
    fi
done
