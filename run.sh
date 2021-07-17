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
    for i in pdf images tsv txt raw work stage output report
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
    for i in ${ROUTE}/pdf/*.pdf
    do
        echo -n ${i}
        FILESTUB=$(basename ${i} | sed 's/.pdf//')
        PDFPATH=${ROUTE}/work/${FILESTUB}.pdf
        if [ ! -f ${PDFPATH} ]; then
            N=$(pdfimages -list ${i} | wc -l)
            if [ ${N} = 2 ]; then
                echo -n " remove grey background"
                gs -q -sstdout=/dev/null -dSAFER -dEmbedAllFonts=true -dNOPAUSE -dBATCH -dPDFA=1 -dNOOUTERSAVE -sProcessColorModel=DeviceCMYK -sPDFACompatibilityPolicy=1 -sDEVICE=pdfwrite -sOutputFile=${PDFPATH} ${i} 2> /dev/null
                qpdf --replace-input --stream-data=uncompress ${PDFPATH}
                (cd ${ROUTE};
                 filter_pdf.py work/${FILESTUB}.pdf;
                 qpdf --no-warn stage/${FILESTUB}.pdf output/${FILESTUB}.pdf)
            fi
        fi
        echo
        TXTPATH=${ROUTE}/txt/${FILESTUB}.txt
        if [ ! -f ${TXTPATH} ]; then
            pdftotext -layout -nopgbrk ${i} ${TXTPATH}
        fi
    done
    if [ -z "$(ls -A ${ROUTE}/report/)" ]; then
        echo Create gauge report ${ROUTE}
        ./collate-gauge.py ${ROUTE}
    fi
    find ${ROUTE} -name \*.tsv -exec sed -i 's/\t$//' {} \;
done

for ROUTE in $(jq -r '.[] | keys[]' section-list.json)
do
    echo Create PNG images ${ROUTE}
    for i in ${ROUTE}/output/*.pdf
    do
        FILESTUB=$(basename ${i} | sed 's/.pdf//')
        echo -n ${ROUTE} ${FILESTUB}.png
        if [ ! -f ${ROUTE}/images/${FILESTUB}.png ]; then
            echo -n " generate"
            pdftoppm -singlefile -r 300 -png ${i} ${ROUTE}/images/${FILESTUB}
        fi
        echo
    done
done

echo Create md files
if [ ! -z Anglia/anglia-text.md ]; then
    ./format-md.py
fi
