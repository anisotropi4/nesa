#!/usr/bin/env bash

ROUTE=$1

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
