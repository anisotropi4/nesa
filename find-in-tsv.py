#!/usr/bin/env python

import os
import sys
import pandas as pd
import argparse

PARSER = argparse.ArgumentParser(description='Get text from matching tsv file')
PARSER.add_argument('filepath', type=str, nargs='?', default='Scotland/tsv/pg_1041.tsv', help='name of tsv-file')
PARSER.add_argument('searchstring', type=str, nargs='*', default=['Curve'], help='string to search')

PARSER.add_argument('--csv', dest='csvfile', action='store_true',
                    default=False, help='read CSV separator')

ARGS, _ = PARSER.parse_known_args()
FILEPATH = ARGS.filepath
FILENAME = os.path.basename(FILEPATH)
SEARCHSTRING = ' '.join(ARGS.searchstring).lower()
SEP = '\t'
if ARGS.csvfile:
    SEP = ','

sys.stderr.write(FILENAME)
sys.stderr.write('\n')

try:
    DATA = pd.read_csv(FILEPATH, dtype=str, sep=SEP)
except (pd.errors.EmptyDataError, pd.errors.ParserError):
    sys.exit(1)

DATA = DATA.dropna(how='all').dropna(axis='columns')

for COLUMN in DATA.columns:
    DATA.loc[:, COLUMN] = DATA.loc[:, COLUMN].str.replace(r'\r', ' ')

OUTPUT = []
for COLUMN in DATA.columns:
    idx1 = DATA.loc[:, COLUMN].str.casefold().str.find(SEARCHSTRING) > -1
    for _, r in DATA[idx1].iterrows():
        OUTPUT.append(r.to_list() + [COLUMN])

if OUTPUT:
    print(SEP.join(['filename'] + DATA.columns.to_list() + ['column']))
    for LINE in OUTPUT:
        print(SEP.join([FILENAME] + LINE))
