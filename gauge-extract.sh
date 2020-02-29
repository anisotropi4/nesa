#!/bin/sh

TABULA=1.0.3

TABULADIR=${HOME}/nesa3
PATH=${PATH}:${TABULADIR}

TABULAFILE=tabula-${TABULA}-jar-with-dependencies.jar

FILEPATH=$1
FILEDIR=$(dirname $1)
FILESTUB=$(basename $1 | sed 's/\.pdf$//')

for i in work
do
    if [ ! -d ${i} ]; then
        mkdir ${i}
    fi
done

if [ ! -f work/${FILESTUB}.png ]; then
    convert ${FILEPATH} -flatten -negate -threshold 1% -negate work/${FILESTUB}.png
fi

echo $(basename $1)

set -- lattice stream lattice

N=1
if [ ! -f ${FILESTUB}_${N}.tsv ]; then
    for P in $(rectangles3.py work/${FILESTUB}.png)
    do
        echo ${P}
        XFLAG=$1
        java -Dfile.encoding=utf-8 -Xms256M -Xmx2048M -jar ${TABULADIR}/${TABULAFILE} --area ${P} --${XFLAG} -f TSV -o ${FILESTUB}_${N}.tsv ${FILEDIR}/${FILESTUB}.pdf
        N=$((N+1))
        shift        
    done
fi
