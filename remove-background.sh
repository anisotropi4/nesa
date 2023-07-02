#!/bin/bash

IFS=$'\012'
ROUTE=$1
export NESADIR=${PWD}
export PATH=${PATH}:${NESADIR}

source venv/bin/activate

for i in ${ROUTE}/pdf/*.pdf
do
    FILESTUB=$(basename ${i} | sed 's/.pdf//')
    PDFPATH=${ROUTE}/work/${FILESTUB}.pdf
    if [ ! -f ${PDFPATH} ]; then
        N=$(pdfimages -list ${i} | wc -l)
        if [ ${N} = 2 ]; then
            #echo -n ${i}
            #echo -n " remove grey background"
            gs -q -sstdout=/dev/null -dSAFER -dEmbedAllFonts=true \
               -dNOPAUSE -dBATCH -dPDFA=1 -dNOOUTERSAVE \
               -sProcessColorModel=DeviceGray -sColorConversionStrategy=Gray \
               -sPDFACompatibilityPolicy=1 -sDEVICE=pdfwrite \
               -sOutputFile=${PDFPATH} ${i} 2> /dev/null
            qpdf --replace-input --stream-data=uncompress ${PDFPATH}
            (cd ${ROUTE};
             filter_pdf.py work/${FILESTUB}.pdf;
             qpdf --no-warn stage/${FILESTUB}.pdf output/${FILESTUB}.pdf)
            #echo
        fi
    fi
done
