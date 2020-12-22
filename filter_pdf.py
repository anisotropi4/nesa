#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-

import argparse
import re
from os.path import basename, dirname

PARSER = argparse.ArgumentParser(description='Filter backgrounds from PDFs')
PARSER.add_argument('filename', type=str, nargs='?', default='pg_0897.pdf', help='name of pdf-file')

ARGS, _ = PARSER.parse_known_args()
FILEPATH = ARGS.filename
FILEDIR = dirname(FILEPATH)
FILENAME = basename(FILEPATH)

with open(FILEPATH, 'rb') as fin:
    DATA = fin.read()

def get_decode(data):
    try:
        return data.decode().rstrip()
    except UnicodeDecodeError:
        return data

def get_lines(data):
   b = [0] + [i + 1 for i, c in enumerate(list(data)) if c == ord('\n')]
   return [data[i:j] for i, j in zip(b[:-1], b[1:])]

LINES = get_lines(DATA)

START = False
FSTAR = False
POP = False
OUTPUT = LINES.copy()
m = 0
for n, v in enumerate(LINES):
    block = get_decode(v)
    if isinstance(block, bytes):
        POP = False
        continue
    if block == 'stream':
        START = True
        continue
    if not START:
        continue
    if len(block) > 8:
        continue
    if 'q' in block.lower():
        if POP:
            OUTPUT[m:n] = [None] * (n - m)
        m = n + 1
        POP = False
        FSTAR = False
    if '1 1 0 rg' in block:
        POP = True
        FSTAR = False
    if 'f*' in block:
        POP = not FSTAR
        FSTAR = True

with open('stage/{}'.format(FILENAME), 'wb') as fout:
    for i in OUTPUT:
        if i is None:
            continue
        if isinstance(i, bytes):
            fout.write(i)
            continue
        if isinstance(i, str):
            fout.write(i.encode())
            fout.write(b'\n')
            continue
