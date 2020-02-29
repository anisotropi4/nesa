#!/bin/sh

TABULA=1.0.3

TABULAFILE=tabula-${TABULA}-jar-with-dependencies.jar

if [ ! -f ${TABULAFILE} ]; then
    echo downloading ${TABULAFILE}
    curl -L https://github.com/tabulapdf/tabula-java/releases/download/v${TABULA}/${TABULAFILE} -o ${TABULAFILE} 
fi

ROUTE=$1
cd ${ROUTE}

for i in tsv stream
do
    if [ ! -d ${i} ]; then
        mkdir ${i}
    fi
done


if [ ! -d pdf ]; then
    echo No pdf directory
    exit 1
fi

for FILE in $(cd pdf; ls *.pdf | sed 's/.pdf//')
do
    if [ ! -s stream/${FILE}.tsv ]; then
        java -Dfile.encoding=utf-8 -Xms256M -Xmx2048M -jar ../${TABULAFILE} -t -f TSV -o stream/${FILE}.tsv pdf/${FILE}.pdf
    fi
    if [ ! -f tsv/${FILE}.tsv ]; then
        java -Dfile.encoding=utf-8 -Xms256M -Xmx2048M -jar ../${TABULAFILE} -l -f TSV -o tsv/${FILE}.tsv pdf/${FILE}.pdf
        if [ ! -s tsv/${FILE}.tsv ]; then
            echo WARNING: processing lattice "pdf/${FILE}.pdf" with page cut
            java -Dfile.encoding=utf-8 -Xms256M -Xmx2048M -jar ../${TABULAFILE} -l --area 210,0,3500,2500 -f TSV -o tsv/${FILE}.tsv pdf/${FILE}.pdf
        fi
    fi
done
