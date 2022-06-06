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
#PARSER.add_argument('route', type=str, nargs='?', default='Western', help='name of route')
#PARSER.add_argument('route', type=str, nargs='?', default='Kent-Sussex-Wessex', help='name of route')
PARSER.add_argument('route', type=str, nargs='?', default='London-North-Western-South', help='name of route')

ARGS, _ = PARSER.parse_known_args()
ROUTE = dirname(ARGS.route) or ARGS.route

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
    return sorted(files)

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
    start = filelist[0]
    filelist = sorted([i for k in ['LIST OF MODULE PAGES AND DATES', 'LOCAL INSTRUCTIONS'] for i in get_files(k, fpath) if i > start])
    end = filelist[0] if len(filelist) > 0 else None
    return (start, end)

RO = re.compile('( [0]+)|:$')
RA = re.compile('[^\w ]')
RM = re.compile(r'(^[oO][oO0]+)|( [oO0][oO0]+)|([oO][oO0]+$)')
WS = re.compile(r'\s+')

def filter(data):
    return [None if j is None or WS.sub('', j) == '' else RM.sub('', WS.sub(' ', j)) for j in data]

def get_font(pdf):
    for k, font in pdf.device.rsrcmgr._cached_fonts.items():
        if 'CharSet' in font.descriptor:
            return partial(font.to_unichr)

def get_edge(this_df, c, t=' – '):
    edge = this_df[c].str.rsplit(t, 1, expand=True)
    this_df.insert(2, 'to', edge[1])
    this_df.insert(2, 'from', edge[0])
    for s in [' - ', ' –', ' to ']:
        IDX1 = (this_df['to'].isnull()) & (this_df[c].str.find(s) != -1)
        if IDX1.any():
            this_df.loc[IDX1, ['from', 'to']] = this_df.loc[IDX1, c].str.rsplit(s, 1, expand=True).values
    return this_df.fillna('')

def get_key(v):
    #k = ':'.join([i.strip().lower() for i in v])
    k = v.str.lower().str.cat(sep=':')
    k = RO.sub('', k).replace(' ', '')
    k = k.replace('loco gauge', 'gauge')
    for v in [':m:', ':om:', ':ch:', ':och:']:
        k = k.replace(v, '::')
    for v in [':noteso', ':notes', ':note']:
        k = k.replace(v, '')
    return k

def get_mch(this_series):
    return this_series.str.contains('^M|Ch$', flags=re.IGNORECASE, regex=True)

def get_table(page, table_settings={'snap_tolerance': 8}):
    table = page.extract_table(table_settings)
    if DEBUG:
        img = page.to_image()
        img.reset().debug_tablefinder(table_settings)
        img.save('debug.png')
    if table:
        data = [filter(i) for i in table]
        df = pd.DataFrame(data)
        df = df.replace('', pd.NA).dropna(how='all').dropna(how='all', axis=1)
        df = df.reset_index(drop=True).fillna('')
        if not isinstance(df.columns, pd.RangeIndex):
            df.columns = pd.RangeIndex(df.shape[1])
        for s in [' – ', ' to ']:
            if (df[1].str.find(s) > -1).any():
                return get_edge(df, 1, s)
            if (df[2].str.find(s) > -1).any():
                return get_edge(df, 2, s)
        sys.stderr.writelines('ERROR: no edge {}\n'.format(f))
        return df
    return pd.DataFrame()

def get_page(filepath):
    p = re.compile('[._]')
    return p.split(filepath)[-2]

DEBUG = True
DEBUG = False

FILES = get_filelist(ROUTE)
START, END, *_ = FILES + (None, )
START = START.replace('txt', 'output')
END = END.replace('txt', 'output') if END else None
ALLFILES = list_files(dirname(START))
PDFFILES = [i for i in ALLFILES if i[-4:].lower() == '.pdf']
FILELIST = sorted(f for f in PDFFILES if f > START and (not END or f < END))
REPORTS = {}

if DEBUG:
    #FILELIST = ['Anglia-Route/output/pg_0439.pdf']
    #FILELIST = ['Kent-Sussex-Wessex/output/pg_0830.pdf']
    #FILELIST = ['Kent-Sussex-Wessex/output/pg_0844.pdf']
    #FILELIST = ['Kent-Sussex-Wessex/output/pg_0868.pdf']
    #FILELIST = ['Kent-Sussex-Wessex/output/pg_0898.pdf']
    #FILELIST = ['London-North-Eastern/output/pg_1031.pdf']
    #FILELIST = ['London-North-Eastern/output/pg_1054.pdf']
    #FILELIST = ['London-North-Eastern/output/pg_1035.pdf']
    #FILELIST = ['London-North-Eastern/output/pg_1052.pdf']
    #FILELIST = ['London-North-Western-North/output/pg_0921.pdf']
    FILELIST = ['London-North-Western-South/output/pg_0090.pdf']
    #FILELIST = ['London-North-Western-South/output/pg_0521.pdf']
    #FILELIST = ['London-North-Western-South/output/pg_0538.pdf']
    #FILELIST = ['Kent-Sussex-Wessex/output/pg_0884.pdf']
    #FILELIST = ['Scotland/output/pg_1049.pdf']
    #FILELIST = ['Scotland/output/pg_1086.pdf']
    #FILELIST = ['Western-and-Wales/output/pg_0789.pdf']
    #FILELIST = ['Western-and-Wales/output/pg_0790.pdf']
    ROUTE = FILELIST[0].split('/')[0]

def get_tablename(p):
    pages, tablename = list(zip(*[(get_page(i), j) for i, j in TABLELIST]))
    n = [i for i, j in enumerate(pages[1:]) if p < j]
    n += [len(tablename) - 1]
    try:
        return tablename[n[0]]
    except IndexError:
        return None

def fix_ln_header(this_df):
    try:
        mch_0 = get_mch(this_df.iloc[0])
        this_df.iloc[1] = this_df.iloc[1].str.replace('^o', '', regex=True)
        if this_df.iloc[1].any() == '':
            this_df = this_df.drop([1]).reset_index(drop=True)
        mch_1 = get_mch(this_df.iloc[1])
        if not(mch_0.any() or mch_1.any()):
            this_lor = this_df.index[this_df[0].str.contains('line of route', case=False)]
            if not this_lor.empty:
                idx_n = this_df.index
                lor_n = this_lor.values[0]
                mch_n = get_mch(this_df.loc[lor_n + 1])
                if mch_n.any():
                    idx_n = idx_n.insert(0, mch_n.name)
                idx_n = idx_n.insert(0, lor_n).drop_duplicates()
                this_df = this_df.loc[idx_n].reset_index(drop=True)
                mch_0 = get_mch(this_df.iloc[0])
                mch_1 = get_mch(this_df.iloc[1])
        if this_df.loc[1, mch_1].count() in [2, 3]:
            if this_df.loc[1, mch_1].count() == 2:
                this_df = get_table(p0, table_settings={'snap_tolerance': 6})
            elif this_df.loc[1, mch_1].count() == 3:
                this_df = get_table(p0, table_settings={'snap_tolerance': 7})
            mch_1 = get_mch(this_df.iloc[1])
            dc = this_df.columns[mch_1]
            #this_df[dc] = this_df[dc].replace(to_replace=' ', value='', regex=True)
            this_df.iloc[1] = this_df.iloc[1].str.replace('^o', '', regex=True)
            mch_1 = get_mch(this_df.iloc[1])
        if this_df.loc[1, mch_1].count() == 4:
            if not mch_0.any() or this_df.loc[0, mch_0].count() != 4:
                this_df.loc[0, mch_1] = this_df.loc[1, mch_1]
            this_df = this_df.drop([1])
    except IndexError:
        pass
    this_df.iloc[0] = this_df.iloc[0].str.replace(' [0o]$', '', regex=True)
    this_df.iloc[0] = this_df.iloc[0].str.replace('^ +', '', regex=True)
    this_df.iloc[0, -1] = this_df.iloc[0, -1].replace('325', 'Notes')
    return this_df

TABLELIST = get_tabledata('{}/txt'.format(ROUTE))
TABLELOOKUP = {}

print('Extract gauge data for {}'.format(ROUTE))

for f in FILELIST:
    p = get_page(f)
    print(f)
    pdf = pp.open(f)
    p0 = pdf.pages[0]
    df = get_table(p0)
    if not df.empty:
        df = fix_ln_header(df)
        df.insert(0, 'page', p)
        df.insert(0, 'route', ROUTE)
        df.to_csv('{}/tsv/pg_{}.tsv'.format(ROUTE, p), index=False, header=False, sep='\t')
        key = df.iloc[0].str.cat(sep=':')
        if 'Line of Route' in key:
            this_key = get_key(df.iloc[0, 6:])
        if ROUTE == 'London-North-Eastern' and ':note' not in this_key and ':325' in this_key:
            this_key = re.sub(':325$', '', this_key)
        if this_key not in REPORTS:
            df.iloc[0, 0:2] = ['route', 'page']
            df.iloc[0, 4:6] = ['from', 'to']
            REPORTS[this_key] = pd.DataFrame()
            k = get_tablename(p)
            if k not in TABLELOOKUP:
                TABLELOOKUP[k] = []
            TABLELOOKUP[k].append(this_key)
        REPORTS[this_key] = pd.concat([REPORTS[this_key], df])
        with open('{}/raw/pg_{}.txt'.format(ROUTE, p), 'w') as fout:
            fout.write(p0.extract_text())

for i, k in enumerate(REPORTS):
    REPORTS[k].to_csv('{}/report/gauge-report-{}.tsv'.format(ROUTE, str(i).zfill(2)), sep='\t', index=False, header=False)


def get_dataframe(this_df):
    if 'Line of Route' in this_df.iloc[0, 6]:
        this_df.iloc[0, 7:11] = ['M', 'Ch','M', 'Ch']
    this_df = this_df.drop_duplicates(subset=[i for i in this_df.columns if i not in ['route', 'page', 'from', 'to']])
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
