#!/usr/bin/env python
# -*- coding: iso-8859-1 -*-
"""filter_pdf.py: filter GhostScript greyscale and background colour from PDF"""

import argparse
import re
from os.path import basename

PARSER = argparse.ArgumentParser(description="Filter background shading from PDF files")
PARSER.add_argument(
    "filename",
    type=str,
    nargs="?",
    default="Scotland/work/pg_1125.pdf",
    help="name of pdf-file",
)

ARGS, _ = PARSER.parse_known_args()
FILEPATH = ARGS.filename
FILENAME = basename(FILEPATH)

FILEPATH = f"{FILEPATH}"
with open(FILEPATH, "rb") as fin:
    DATA = fin.read()


def get_decode(data):
    """get_decode: decode binary data to string and remove whitespace"""
    try:
        return data.decode().rstrip()
    except UnicodeDecodeError:
        return data


def get_lines(data):
    """get_lines: line-break binary data into list of enumerated lines"""
    b = [0] + [i + 1 for i, c in enumerate(list(data)) if c == ord("\n")]
    return [data[i:j] for i, j in zip(b[:-1], b[1:])]


# Match ^[+-]d[.d]+ [r]g$ or ^[+-]d[.d] [+-]d[.d] [+-]d[.d] [r]g$
GBLOCK = re.compile(
    r"^(?P<d1>[+-]?(\d+(\.\d*)?|\.\d+)) "
    r"((?P<d2>[+-]?(\d+(\.\d*)?|\.\d+)) "
    r"(?P<d3>[+-]?(\d+(\.\d*)?|\.\d+)) )?(?P<f>r?g$)"
)

LINES = get_lines(DATA)
START = False
# FSTAR = False
OUTPUT = LINES.copy()
for n, v in enumerate(LINES):
    block = get_decode(v)
    if isinstance(block, bytes):
        continue
    if block == "stream":
        START = True
        continue
    if not START:
        continue
    if len(block) > 64:
        continue
    u = GBLOCK.match(block)
    if u is None:
        continue
    u = u.groupdict()
    r = None
    if u["f"] == "g" and "0" not in u.values() and "1" not in u.values():
        r = "1 g\n"
        if float(u["d1"]) < 0.7:
            r = "0 g\n"
    if u["f"] == "rg" and "0" in u.values():
        r = "1 g\n"
    if r is not None:
        OUTPUT[n] = r.encode()


with open(f"stage/{FILENAME}", "wb") as fout:
    for i in OUTPUT:
        if i is None:
            continue
        if isinstance(i, bytes):
            fout.write(i)
            continue
        if isinstance(i, str):
            fout.write(i.encode())
            fout.write(b"\n")
