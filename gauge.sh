#!/bin/bash


export PATH=${PATH}:${HOME}/nesa3

ROUTE=$(basename $1)
cd ${ROUTE}

if [ x"${ROUTE}" = x ]; then
    echo ERROR: No route
    exit 1
fi

for i in gauge
do
    if [ ! -d ${i} ]; then
        mkdir -p ${i}
    fi
done

cd gauge

for i in ../pdf/*.pdf
do
    gauge-extract.sh ${i}
done
