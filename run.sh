#!/bin/bash -x

IFS=$'\012'

for FILE in $(ls download/*Sectional\ Appendix*.pdf | sed 's/^download\///')
do
    echo "${FILE}	$(echo ${FILE} | sed 's/ Sectional Appendix .*.pdf//; s/[,)(]//g; s/ /-/g')"
done | jq -Rsc 'split("\n")[0:-1] | map([split("\t")][] | {(.[1]): (.[0])})' > section-list.json

for i in $(jq -c '.[]' section-list.json)
do
    ROUTE=$(echo ${i} | jq -r 'keys[]')
    for j in download pdf tsv images work output
    do
        if [ ! -d ${ROUTE}/${j} ]; then
            mkdir -p ${ROUTE}/${j}
        fi
    done

    FILE=$(echo ${i} | jq -r 'values[]')
    if [ ! -f "${ROUTE}/pdf/${FILE}" ]; then
        ln "download/${FILE}" "${ROUTE}/download/${FILE}"
    fi

    if [ ! -f ${ROUTE}/pdf/pg_0001.pdf ]; then
         (cd ${ROUTE}/pdf; pdfseparate "../download/${FILE}" pg_%04d.pdf)
    fi
done

for SCRIPT in ocr3.sh tabula.sh
do
    for ROUTE in $(jq -cr '.[] | keys[]' section-list.json)
    do
        ./${SCRIPT} ${ROUTE}
    done
done
