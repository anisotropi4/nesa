#!/bin/bash

export TESSDATA_PREFIX=${HOME}/tesseract/share/tessdata
export PATH=${HOME}/tesseract/bin:${PATH}

which tesseract

ROUTE=$(basename $1)
cd ${ROUTE}

if [ x"${ROUTE}" = x ]; then
    echo ERROR: No route
    exit 1
fi

find . -size 0 -exec rm {} \;

for i in pdf work output report images/archive
do
    if [ ! -d ${i} ]; then
        mkdir -p ${i}
    fi
done

echo Stage 1
for i in $(cd pdf; ls pg_*.pdf | sed 's/^pg_//; s/.pdf$//')
do
    if [ ! -f images/pg_${i}-000.png ]; then
        pdfimages -all pdf/pg_${i}.pdf images/pg_${i}
    fi
done

echo Stage 2
for IMAGE in $(ls images/pg_????-005* 2> /dev/null | sed 's/images\///; s/-005.*$//')
do
    mv images/${IMAGE}-* images/archive
    convert images/archive/${IMAGE}*.png -append images/${IMAGE}-000.png
done

echo Stage 3
for FILE in $(cd images; ls pg_????-000.png | sed 's/-000.png$//')
do
    if [ ! -f output/${FILE}.jsonl ]; then
        echo ${ROUTE}/images/${FILE}-000.png
        ../get-text.py --threshold 128 --rotate images/${FILE}-000.png
    fi
done
