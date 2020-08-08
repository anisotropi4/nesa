#!/usr/bin/env python

from os import walk
from os.path import basename, dirname
import re
import sys
import json
import argparse
import pandas as pd
import pdfplumber as pp

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

if ROUTE not in ROUTES:
    sys.stderr.writelines('ERROR: no route {}\n'.format(ROUTE))

def get_filelist(route):
    files = get_files('ROUTE CLEARANCE', '{}/txt'.format(route))
    fpath = dirname(files[0])
    filelist = tuple(f for f in files if string_in_file('Table of Contents', f))
    return filelist + tuple(s for s in get_files('LOCAL INSTRUCTIONS', fpath) if s > files[0])

RO = re.compile('( [0]+)')
RA = re.compile('[^\w ]')

def filter(data):
    ro = re.compile(r'(^[oO][oO0]+)|( [oO0][oO0]+)|([oO][oO0]+$)')
    ws = re.compile(r'\s+')
    return [None if j is None or ws.sub('', j) == '' else ro.sub('', ws.sub(' ', j)) for j in data]

def get_font(pdf):
    for k, font in pdf.device.rsrcmgr._cached_fonts.items():
        if 'CharSet' in font.descriptor:
            return partial(font.to_unichr)
     
def get_gauge(table):
    data = [filter(i) for i in table]
    df = pd.DataFrame(data)
    df = df.loc[:, df[1:].any()]
    df = df.dropna(how='all').dropna(how='all', axis=1).fillna('')
    if not isinstance(df.columns, pd.RangeIndex):
        df.columns = pd.RangeIndex(df.shape[1])
    return df

def get_edge(this_df, c):
    edge = this_df[c].str.rsplit(' – ', 1, expand=True)
    this_df.insert(2, 'to', edge[1])
    this_df.insert(2, 'from', edge[0])
    for s in [' - ', ' –']:
        IDX1 = (this_df['to'].isnull()) & (this_df[c].str.find(s) != -1)
        if IDX1.any():
            this_df.loc[IDX1, ['from', 'to']] = this_df.loc[IDX1, c].str.rsplit(s, 1, expand=True).values
    return this_df.fillna('')

def get_key(v):
    k = ':'.join([i.strip().lower() for i in v])
    k = RO.sub('', k).replace(' ', '')
    k = k.replace('loco gauge', 'gauge')
    for v in [':m:', ':om:', ':ch:', ':och:']:
        k = k.replace(v, '::')
    for v in [':noteso', ':notes', ':note']:
        k = k.replace(v, '')
    return k
        
def get_table(page, table_settings={'snap_tolerance': 8}):
    table = page.extract_table(table_settings)
    if DEBUG:
        img = p0.to_image()
        img.reset().debug_tablefinder(table_settings)
        img.save('debug.png')
    if table:
        df = get_gauge(table)
        if (df[1].str.find(' – ') > -1).any():
            return get_edge(df, 1)
        if (df[2].str.find(' – ') > -1).any():
            return get_edge(df, 2)
        sys.stderr.writelines('ERROR: no edge {}\n'.format(f))
        return df
    return pd.DataFrame()

def get_page(filepath):
    p = re.compile('[._]')
    return p.split(filepath)[-2]
    
DEBUG=True
DEBUG=False

FILES = get_filelist(ROUTE)
START, END, *_ = FILES + (None, )
START = START.replace('txt', 'stage')
END = END.replace('txt', 'stage') if END else None
ALLFILES = list_files(dirname(START))
FILELIST = sorted(f for f in ALLFILES if f > START and (not END or f < END))
REPORTS = {}

if DEBUG:
    #FILELIST = ['Anglia-Route/stage/pg_0466.pdf']
    FILELIST = ['London-North-Eastern/stage/pg_1031.pdf']

def get_tablename(p):
    pages, tablename = list(zip(*[(get_page(i), j) for i, j in TABLELIST]))
    n = [i for i, j in enumerate(pages[1:]) if p < j]
    n += [len(tablename) - 1]
    try:
        return tablename[n[0]]
    except IndexError:
        return None

TABLELIST = get_tabledata('{}/txt'.format(ROUTE))
TABLELOOKUP = {}

for f in FILELIST:
    print(f)
    pdf = pp.open(f)
    p0 = pdf.pages[0]
    p = get_page(f)
    df = get_table(p0)
    if not df.empty:
        df.insert(0, 'page', p)
        df.insert(0, 'route', ROUTE)
        df.to_csv('{}/tsv/pg_{}.tsv'.format(ROUTE, p), index=False, header=False, sep='\t')
        key = ':'.join(df.iloc[0].values)
        if 'Line of Route' in key:
            this_key = get_key(df.iloc[0, 6:])
        if this_key not in REPORTS:
            df.iloc[0, 0:2] = ['route', 'page']
            df.iloc[0, 4:6] = ['from', 'to']
            REPORTS[this_key] = pd.DataFrame()
            k = get_tablename(p)
            if k not in TABLELOOKUP:
                TABLELOOKUP[k] = []
            TABLELOOKUP[k].append(this_key)
        REPORTS[this_key] = REPORTS[this_key].append(df)
        with open('{}/output/pg_{}.txt'.format(ROUTE, p), 'w') as fout:
            fout.write(p0.extract_text())

for i, k in enumerate(REPORTS):        
    REPORTS[k].to_csv('{}/report/gauge-report-{}.tsv'.format(ROUTE, str(i).zfill(2)), sep='\t', index=False, header=False)

def get_dataframe(this_df):
    if 'Line of Route' in this_df.iloc[0, 6]:
        this_df.iloc[0, 7:11] = ['M', 'Ch','M', 'Ch']
    for i in [1, 2]:
        if this_df[i].str.match('Line of Route').any():
            return this_df.drop_duplicates(subset=[i])
    return this_df

with pd.ExcelWriter('{}/{}-clearance.xlsx'.format(ROUTE, ROUTE.lower())) as writer:
    for w, k in TABLELOOKUP.items():
        stub = ' '.join(RA.sub('', w).split())
        s = stub
        for i, v in enumerate(k):
            df = get_dataframe(REPORTS[v])
            if len(k) > 1:
                s = stub + ' ' + str(i+1)
            df.to_excel(writer, s, index=False, header=False)
