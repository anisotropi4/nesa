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
    echo Process ${ROUTE} PDF pages
    ./pdf-separate.sh ${ROUTE}
    ./remove-background.sh ${ROUTE}
    ./generate-txt.sh ${ROUTE}
    if [ -z "$(ls -A ${ROUTE}/*-clearance.xlsx 2> /dev/null)" ]; then
        echo Create gauge report ${ROUTE}
        ./collate-gauge2.py ${ROUTE}
    fi
done

for ROUTE in $(jq -r '.[] | keys[]' section-list.json)
do
    ./generate-png.sh ${ROUTE}
done

echo Create md files
if [ ! -z Anglia/anglia-text.md ]; then
    ./format-md.py
fi
