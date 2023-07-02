#!/bin/bash

IFS=$'\012'

source venv/bin/activate
export NESADIR=${PWD}
export PATH=${PATH}:${NESADIR}

if [ ! -s section-list.json ]; then
    for FILEPATH in $(ls download/*Sectional\ Appendix*.pdf)
    do
        FILENAME=$(basename ${FILEPATH})
        ROUTE=$(echo ${FILENAME} | sed 's/ Sectional Appendix .*.pdf//; s/[,)(]//g; s/Sussex and Wessex/Sussex-Wessex/; s/ /-/g')
        echo "{"\"${ROUTE}\": \"${FILENAME}\""}"
    done | jq -cs '.' > section-list.json
fi

for ROUTE in $(jq -r '.[] | keys[]' section-list.json)
do
    echo Processing ${ROUTE}
    for i in pdf images tsv ftsv txt ftxt raw work stage output report dump
    do
        if [ ! -d ${ROUTE}/${i} ]; then
            mkdir -p ${ROUTE}/${i}
        fi
    done
    FILENAME=$(jq -r '.[] | select(. | keys[] == "'${ROUTE}'") | .[]' section-list.json)
    if [ -z "$(ls -A ${ROUTE}/pdf/)" ]; then
        echo Extract PDF pages ${ROUTE}
        (cd ${ROUTE}/pdf; pdfseparate "../../download/${FILENAME}" pg_%04d.pdf)
    fi    
    echo Process ${ROUTE} PDF pages
    ./remove-background.sh ${ROUTE}
    for i in ${ROUTE}/pdf/*.pdf
    do
        FILESTUB=$(basename ${i} | sed 's/.pdf//')
        TXTPATH=${ROUTE}/txt/${FILESTUB}.txt
        if [ ! -f ${TXTPATH} ]; then            
            pdftotext -layout -nopgbrk ${i} ${TXTPATH}
        fi
        PDFPATH=${i}
        OUTPUTPATH=${ROUTE}/output/${FILESTUB}.pdf
        if [ -f ${OUTPUTPATH} ]; then
            PDFPATH=${OUTPUTPATH}
        fi
        TXTPATH=${ROUTE}/ftxt/${FILESTUB}.txt
        if [ ! -f ${TXTPATH} ]; then
           pdftotext -fixed 2.8 -nopgbrk ${PDFPATH} ${TXTPATH}
        fi
    done
    if [ -z "$(ls -A ${ROUTE}/report/)" ]; then
        echo Create gauge report ${ROUTE}
        ./collate-gauge2.py ${ROUTE}
    fi
    #find ${ROUTE} -name \*.tsv -exec sed -i 's/\t$//' {} \;
done

for ROUTE in $(jq -r '.[] | keys[]' section-list.json)
do
    echo Create PNG images ${ROUTE}
    for i in ${ROUTE}/output/*.pdf
    do
        FILESTUB=$(basename ${i} | sed 's/.pdf//')
        if [ ! -f ${ROUTE}/images/${FILESTUB}.png ]; then
                echo -n ${ROUTE} ${FILESTUB}.png
            echo -n " generate"
            pdftoppm -singlefile -r 300 -png ${i} ${ROUTE}/images/${FILESTUB}
            echo
        fi
    done
done

echo Create md files
if [ ! -z Anglia/anglia-text.md ]; then
    ./format-md.py
fi
