#!/bin/bash

IFS=$'\012'

export NESADIR=${PWD}
export PATH=${PATH}:${NESADIR}

if [ ! -d venv ]; then
    echo Set up python3 virtual environment
    python3 -m venv venv
    source venv/bin/activate
    pip3 install --upgrade pip
    pip3 install -r requirements.txt
else
    source venv/bin/activate
fi

if [ ! -s section-list.json ]; then
    for FILEPATH in $(ls download/*.pdf)
    do
        FILENAME=$(basename ${FILEPATH})
        ROUTE=$(echo ${FILENAME} | sed 's/ Sectional Appendix .*.pdf//; s/[,)(]//g; s/Sussex and Wessex/Sussex-Wessex/; s/Western North.*/Western North/; s/ /-/g')
        echo "{"\"${ROUTE}\": \"${FILENAME}\""}"
    done | jq -cs '.' > section-list.json
fi

for ROUTE in $(jq -r '.[] | keys[]' section-list.json)
do
    echo Processing ${ROUTE}
    for i in pdf images tsv txt raw work stage output report 
    do
        if [ ! -d ${ROUTE}/${i} ]; then
            mkdir -p ${ROUTE}/${i}
        fi
    done
    FILENAME=$(jq -r '.[] | select(. | keys[] == "'${ROUTE}'") | .[]' section-list.json)
    if [ -z "$(ls -A ${ROUTE}/pdf/)" ]; then
        echo Extract PDF pages ${ROUTE}
        (cd ${ROUTE}/pdf; pdfseparate "../../download/${FILENAME}" pg_%04d.pdf 2> /dev/null)
    fi    
    echo Process ${ROUTE} PDF pages
    ./remove-background.sh ${ROUTE}
    for i in ${ROUTE}/pdf/*.pdf
    do
        FILESTUB=$(basename ${i} | sed 's/.pdf//')
        PDFPATH=${i}
        OUTPUTPATH=${ROUTE}/output/${FILESTUB}.pdf
        if [ -f ${OUTPUTPATH} ]; then
            PDFPATH=${OUTPUTPATH}
        fi
        TXTPATH=${ROUTE}/txt/${FILESTUB}.txt
        if [ ! -f ${TXTPATH} ]; then
            pdftotext -fixed 8 -nopgbrk ${PDFPATH} ${TXTPATH}
        fi
    done
    if [ -z "$(ls -A ${ROUTE}/*-clearance.xlsx 2> /dev/null)" ]; then
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
            #echo -n ${ROUTE} ${FILESTUB}.png
            #echo -n " generate"
            pdftoppm -singlefile -r 300 -png ${i} ${ROUTE}/images/${FILESTUB}
            #echo
        fi
    done
done

echo Create md files
if [ ! -z Anglia/anglia-text.md ]; then
    ./format-md.py
fi
