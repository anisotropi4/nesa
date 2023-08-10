#!/usr/bin/env bash

ROUTE=$1
echo Extract PDF pages ${ROUTE}
if [ -z "$(ls -A ${ROUTE}/pdf/)" ]; then
    PDFNAME=$(jq -r '.[] | select(. | keys[] == "'${ROUTE}'") | .[]' section-list.json)

    (cd ${ROUTE}/pdf; pdfseparate "../../download/${PDFNAME}" pg_%04d.pdf) 2> /dev/null
fi    
