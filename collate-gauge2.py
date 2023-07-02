#!/usr/bin/env python
"""collate-gauge2:  """

import argparse
import json
import re
import sys
from os import path, walk

import cv2
import numpy as np
import pandas as pd
import pdfplumber as pp
from pdf2image import convert_from_path

pd.set_option("display.max_columns", None)

PARSER = argparse.ArgumentParser(description="Extract data from PDFs")
# PARSER.add_argument('route', type=str, nargs='?', default='Western', help='name of route')
# PARSER.add_argument(
#    "route", type=str, nargs="?", default="Kent-Sussex-Wessex", help="name of route"
# )
PARSER.add_argument(
    "route", type=str, nargs="?", default="Anglia", help="name of route"
)
# PARSER.add_argument(
#    "route", type=str, nargs="?", default="Western", help="name of route"
# )


ARGS, _ = PARSER.parse_known_args()
ROUTE = path.dirname(ARGS.route) or ARGS.route


def outer_rectangle(img):
    cannied = cv2.Canny(img, threshold1=50, threshold2=200, apertureSize=7)
    return cv2.findContours(cannied, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)


def list_files(filepath):
    files = ()
    for d, _, filenames in walk(filepath):
        files = files + tuple(f"{d}/{f}" for f in filenames)
    return files


def string_in_file(string, filepath, rline=False):
    with open(filepath, "r", encoding="utf-8") as file_in:
        for i, line in enumerate(file_in):
            if string in line.strip():
                if rline:
                    return (filepath, line.strip())
                return filepath
            if i > 16:
                return None
    return None


def get_files(string, this_path):
    files = ()
    for d, _, filenames in walk(this_path):
        for filename in filenames:
            filepath = string_in_file(string, d + "/" + filename)
            if filepath:
                files += (filepath,)
    return sorted(files)


def get_filedata(this_path):
    with open(this_path, "r", encoding="utf-8") as input_file:
        r = input_file.read()
    return r


with open("section-list.json", "r", encoding="utf-8") as fin:
    ROUTES = sorted({j for i in json.load(fin) for j in i})

if ROUTE not in ROUTES:
    sys.stderr.writelines(f"ERROR: no route {ROUTE}\n")


def get_filelist(route):
    files = get_files("ROUTE CLEARANCE", f"{route}/txt")
    fpath = path.dirname(files[0])
    filelist = tuple(f for f in files if string_in_file("Table of Contents", f))
    start = filelist[0]
    filelist = sorted(
        [
            i
            for k in ["LIST OF MODULE PAGES AND DATES", "LOCAL INSTRUCTIONS"]
            for i in get_files(k, fpath)
            if i > start
        ]
    )
    end = filelist[0] if len(filelist) > 0 else None
    return (start, end)


def get_page(filepath):
    p = re.compile("[._]")
    return p.split(filepath)[-2]


def get_route_list(route):
    files = get_filelist(route)
    start, end, *_ = files + (None,)
    start = start.replace("txt", "output")
    end = end.replace("txt", "output") if end else None
    all_files = list_files(path.dirname(start))
    pdf_files = [i for i in all_files if i[-4:].lower() == ".pdf"]
    return sorted(f for f in pdf_files if f > start and (not end or f < end))


def get_key_name(data, key):
    for i in data.splitlines():
        if key in i:
            return i.strip().split("  ")[0]
    return None


def combine_row(this_df, sep=" "):
    return this_df.fillna("").agg(lambda v: sep.join(v).strip())


def combine_columns(this_df, ix, sep=" "):
    r = this_df.copy()
    for i in ix[::-1]:
        j = r.iloc[:, i].notna()
        j = r.index.get_indexer(r[j].index)
        r.iloc[j, (i - 1)] = r.iloc[j, (i - 1)].fillna("")
        v = (r.iloc[:, (i - 1)] + sep + r.iloc[:, i]).fillna(r.iloc[:, (i - 1)])
        r.iloc[:, (i - 1)] = v
    columns = r.columns.values
    r.columns = range(r.columns.size)
    r = r.drop(r.columns[ix], axis=1)
    # if not pd.api.types.is_numeric_dtype(columns):
    # columns[(ix - 1)] = columns[(ix - 1)] + " " + columns[ix]
    r.columns = [i.strip() for i in columns[r.columns]]
    return r


def get_gaugeframe(this_frame):
    r = this_frame.copy()
    if r.columns.str.contains("Gauge of Route").any():
        return r
    gauge = re.compile(r"Gauge +")
    r.columns = r.columns.str.replace(gauge, "", regex=True)
    return r


def clean_dataframe(this_df):
    r = this_df.copy()
    if r.columns.str.contains("Gauge").any():
        r = get_gaugeframe(this_df)
    update = {
        "C h": "Ch",
        "(MOD) MK3": "MK3 (MOD)",
        "CH": "Ch",
        "Notes R1": "Notes",
        "W10 A": "W10A",
        "W 10": "W10",
        "31/13 1/6": "31/1 31/6",
        "37/03 7/3 37/43 7/6": "37/0 37/3 37/4 37/6",
        "ine of route": "Line of route",
    }
    r = r.rename(columns=update)
    r = r.rename(columns=lambda v: re.sub("Electrification", "", v))
    r.columns = r.columns.str.strip()
    return r.fillna("")


def write_xlsx(route, table_lookup):
    filepath = f"{route}/{route.lower()}-clearance.xlsx"
    keys = sorted(list(table_lookup.keys()))
    count = {i: 1 for i, _ in keys}
    with pd.ExcelWriter(
        filepath
    ) as writer:  # pylint: disable=abstract-class-instantiated
        for k in keys:
            df = pd.concat(table_lookup[k]).reset_index(drop=True)
            key = k[0]
            tab = f"{key}-{str(count[key]).zfill(2)}"
            print(f"{tab}\t\t\t\t{k[1]}")
            df.to_excel(writer, tab, index=False)
            count[key] += 1


def get_area(contour):
    (_, _, width, height) = cv2.boundingRect(contour)
    return (width - 1) * (height - 1)


def get_table_boundary(filepath):
    # 72 dots-per-inch image at 300 dpi
    scale = 72 / 300.0
    image = cv2.imread(filepath)
    if ".pdf" in filepath.lower():
        pages = convert_from_path(filepath, dpi=300, fmt="png")
        image = np.array(pages[0])
    grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    contours, _ = outer_rectangle(grey)
    areas = np.asarray([get_area(i) for i in contours])
    ix = areas.argmax()
    (x1, y1, w1, h1) = np.asarray(cv2.boundingRect(contours[ix]))
    x2 = x1 + w1
    y2 = y1 + h1
    bbox = np.asarray([x1 - 1, y1 - 1, x2 + 1, y2 + 1]) * scale
    return list(bbox)


def get_header(this_df):
    r = this_df.copy()
    lor_match = re.compile(r"^([A-Z]{2}\d{3,5})$")
    m_match = re.compile(r"^\d{1,3}$")
    ix0 = r[0].str.match(lor_match).fillna(False)
    ix1 = r[3].str.match(m_match).fillna(False)
    ix = np.where(~(ix1 | ix0))[0]
    if ix.size == 0:
        return r
    pattern = re.compile(r"[ oO0\n]+((C)\n*([hH])|M)$|[ \n][ oO0\n]+[ \n]*$")
    columns = combine_row(r.loc[ix], "\n")
    if columns.str.contains("W9Plus").any():
        columns = columns.replace(r"(W) (\d) (\d) *", r"\1\2\3", regex=True)
    columns = columns.replace(pattern, r" \1", regex=True)
    columns = columns.replace(r"\n", " ", regex=True).str.strip()
    if not (columns == "").all():
        r.columns = columns
        r = r.drop(ix)
    return r


def get_body(this_df):
    r = this_df.replace(r"\n", " ", regex=True)
    ix = np.where(r.iloc[:, :-1].replace("", pd.NA).isnull().all())[0]
    if pd.api.types.is_numeric_dtype(this_df.columns[ix]):
        r = r.drop(columns=ix)
    r = r.replace("", None)
    r = r.dropna(how="all")
    return r.apply(lambda v: v.str.strip())


def get_table_frame(page, route, tolerance=8, x_tolerance=20):
    table_settings = {"snap_tolerance": tolerance, "join_x_tolerance": x_tolerance}
    filepath = f"{route}/output/pg_{page}.pdf"
    bbox = get_table_boundary(filepath)
    pp_p0 = pp.open(filepath).pages[0]
    table = pp_p0.crop(bbox).extract_table(table_settings)
    r = pd.DataFrame(table)
    if not r.empty:
        r = get_header(r)
        if r.columns[-1] == "" and r.columns[-2] == "Notes":
            n = r.columns.size - 1
            r = combine_columns(r, [n])
        r = get_body(r)
    return r


def fix_tableframe(this_df):
    r = this_df.copy()
    column = np.where(r.isna().any())[0].min()
    ix = np.where(r.iloc[:, column].isna())[0]
    r.iloc[ix, column:-1] = r.iloc[ix, (column + 1) :]
    ix = r.columns[np.where(r.iloc[:, :-1].isna().all())[0]]
    r = r.drop(columns=ix)
    return r


def get_table_name(route, page):
    raw_data = get_filedata(f"{route}/txt/pg_{page}.txt")
    header = "Line of " in raw_data
    skip = "this page is intentionally blank" in raw_data.lower()
    name = get_key_name(raw_data, "Table D")
    return header, skip, name


def set_table(this_table, table_name):
    if not this_table:
        return table_name
    this_table = this_table.replace(" / ", " ").replace("/", " ")
    if table_name:
        print(table_name)
    return this_table


def check_missing_header(this_df, this_header):
    r = this_df.copy()
    try:
        r.columns = this_header
        return True
    except ValueError:
        pass
    return False


def set_missing_header(this_df, this_header):
    r = this_df.copy()
    if check_missing_header(r, this_header):
        r.columns = this_header
        return r
    r = fix_tableframe(r)
    if check_missing_header(r, this_header):
        r.columns = this_header
        return r
    r = r.iloc[:, :-1]
    if check_missing_header(r, this_header):
        r.columns = this_header
        return r
    return pd.DataFrame()


def get_noheader_frame(page, route, this_header):
    r = get_table_frame(page, route, 5)
    if check_missing_header(r, this_header):
        r.columns = this_header
        return r
    if r.iloc[:, -1].isna().all():
        r = r.iloc[:, :-1]
    if check_missing_header(r, this_header):
        r.columns = this_header
        return r
    n = sum(r.isna().any()) // 4
    for _ in range(n):
        s = r.copy()
        r = fix_tableframe(r)
        if check_missing_header(r, this_header):
            r.columns = this_header
            return r
        if r.shape == s.shape:
            break
    r = r.iloc[:, :-1]
    if check_missing_header(r, this_header):
        r.columns = this_header
        return r
    return r


def valid_header(this_df):
    if "" in this_df.columns:
        return False
    header_match = re.compile(" |o$|o[^C]|M C|h M|M {1,}")
    return not any(filter(header_match.match, this_df.columns))


def main(route):
    table_lookup = {}
    print(f"Extract gauge data for {route}")
    table_name, frame_header, lor = None, None, None
    for filepath in get_route_list(route):
        header = False
        p = get_page(filepath)
        print(filepath)
        header, skip, this_table = get_table_name(route, p)
        if skip:
            continue
        df = get_table_frame(p, route)
        if header:
            if valid_header(df):
                frame_header = df.columns
            else:
                df = get_table_frame(p, route, tolerance=6)
                header = valid_header(df)
        if df.empty:
            continue
        table_name = set_table(this_table, table_name)
        if not header:
            if frame_header is None:
                frame_header = pd.Index([i for i in df.columns if i])
            df = set_missing_header(df, frame_header)
            if df.empty:
                df = get_noheader_frame(p, route, frame_header)
        lor = df.iloc[-1, 0]
        if lor.lower() == "note" or " " in lor:
            continue
        df = clean_dataframe(df)
        output = df.copy()
        output.insert(0, "Route", route)
        output.insert(1, "page", p)
        output.to_csv(f"{route}/tsv/pg_{p}.tsv", index=False, sep="\t")
        key = (table_name, ":".join(df.columns))
        print(key)
        try:
            table_lookup[key].append(output)
        except KeyError:
            table_lookup[key] = [output]
    write_xlsx(route, table_lookup)


if __name__ == "__main__":
    main(ROUTE)

# if p == '1115':
# if p == '10918':
# if p == '10920':
# if p == '10955':
# if p == '1008':
# if p == '1046':
# if p == '1046':
# if p == '0927':
# if p == '1062':
# if p == "0395":
# if p == "0394":
# if p == '0890':
# if p == '0885':
# if p == '0895':
# if p == '0988':
# if p == '0444':
# if p == '0446':
#    2 / 0
