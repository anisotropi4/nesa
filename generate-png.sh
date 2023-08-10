#!/usr/bin/env bash

ROUTE=$1

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
