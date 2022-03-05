#!/usr/bin/env python

from os import walk
from itertools import tee
import re
import json
import argparse
import pandas as pd

pd.set_option('display.max_columns', None)

PARSER = argparse.ArgumentParser(description='Extract data from PDFs')
PARSER.add_argument('route', type=str, nargs='?', default='Kent-Sussex-Wessex', help='name of route')

ARGS, _ = PARSER.parse_known_args()
ROUTE = ARGS.route

def list_files(filepath):
    files = ()
    for (d, dirnames, filenames) in walk(filepath):
        files = files + tuple('{}/{}'.format(d, f) for f in filenames)
    return files

def string_in_file(string, filepath, rline=False):
    with open(filepath, 'r') as fin:
        for (i, line) in enumerate(fin):
            if string in line.strip():
                if rline:
                    return (filepath, line.strip())
                return filepath
            if i > 16:
                return None
    return None

def get_files(string, this_path):
    files = ()
    for (d, dirnames, filenames) in walk(this_path):
        for filename in filenames:
            filepath = string_in_file(string, d + '/' + filename)
            if filepath:
                files += (filepath, )
    return files

def get_tabledata(this_path):
    tabledata = ()
    for (d, dirnames, filenames) in walk(this_path):
        for filename in filenames:
            data = string_in_file('Table ', d + '/' + filename, rline=True)
            if data:
                tabledata += (data, )
    return sorted(tabledata)

with open('section-list.json', 'r') as fin:
    ROUTES = sorted({j for i in json.load(fin) for j in i})

def get_page(filepath):
    p = re.compile('[._]')
    return p.split(filepath)[-2]

def prune_link(filepath):
    filestub = filepath.split('/')[1:]
    return '/'.join(filestub)

def get_md(paths):
    return ['[{}]({})'.format(get_page(p), prune_link(p)) for p in paths]

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

def write_md(filename, header, data, M=14):
    with open(filename, 'w') as fout:
        fout.write(header)
        fout.write('|{}|\n'.format('|'.join(['page' for i in range(M)])))
        fout.write('|{}|\n'.format('|'.join(['----' for i in range(M)])))
        for k in [data[i:j] for i, j in pairwise(range(0, len(data) + M, M))]:
            s = (get_md(k)+ [''] * M)[:M]
            fout.write('|{}|\n'.format('|'.join(s)))

for r in ROUTES:
    txtfiles = sorted(get_files('', '{}/txt'.format(r)))
    write_md('{}/{}-text.md'.format(r, r.lower()),
             '# Unformatted text extracted from {} PDF\n\n'.format(r),
             txtfiles)
    tsvfiles = sorted(get_files('', '{}/tsv'.format(r)))
    write_md('{}/{}-tsv.md'.format(r, r.lower()),
             '# Per page Route Clearance TSV from {} PDF\n\n'.format(r),
             tsvfiles,
             M=10)
