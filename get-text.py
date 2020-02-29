#!/usr/bin/env python

import os
import sys
import argparse
import json
import numpy as np
import cv2
import pytesseract as tsrt
import pandas as pd
from itertools import cycle, islice, tee

pd.set_option('display.max_columns', None)

def all_lines(this_img, l=8, gap=16):
    cannied = cv2.Canny(this_img, threshold1=50, threshold2=200, apertureSize=7)
    lines= cv2.HoughLinesP(cannied, rho=1, theta=np.pi / 180, threshold=500, minLineLength=l, maxLineGap=gap)
    if lines is None:
        return lines
    return lines.reshape(-1, 4)

BLUE = (255, 0, 0)
GREEN = (0, 255, 0)
RED = (0, 0, 255)
CYAN = (255, 255, 0)
MAGENTA = (255, 0, 255)
YELLOW = (0, 255, 255)
WHITE = (255, 255, 255)

def draw_rectangle(this_img, p1, p2, colour=GREEN):
    cv2.rectangle(this_img, p1, p2, colour, 1, 8)

def draw_line(this_img, p1, p2, colour=RED):
    cv2.line(this_img, p1, p2, colour, 3, 8)

MODE = 'row'
if __name__ == '__main__':
    MODE = os.path.basename(sys.argv[0])[:-3]

parser = argparse.ArgumentParser(description='Get bounding box')

#parser.add_argument('filename', type=str, nargs='?', default='pg_0087-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0088-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0094-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0096-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0099-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0104-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0149-000.png', help='name of image-file')
parser.add_argument('filename', type=str, nargs='?', default='pg_0176-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0184-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0188-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0199-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0200-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0208-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0210-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0222-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0233-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0244-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0296-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0303-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0314-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0318-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0343-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0442-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0450-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0544-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0655-000.png', help='name of image-file'
#parser.add_argument('filename', type=str, nargs='?', default='pg_0726-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0735-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0785-000.png', help='name of image-file')
#parser.add_argument('filename', type=str, nargs='?', default='pg_0889-000.png', help='name of image-file')

parser.add_argument('--noseq', dest='noseq', action='store_true', help='do not continue file number sequence')

parser.add_argument('--rotate', dest='rotate', action='store_true', help='rotate if height > width')

parser.add_argument('--threshold', dest='threshold', type=float,
                    help='threshold value', default=0.9)

parser.add_argument('--clean', dest='clean', action='store_true', help='clean image')

args, _ = parser.parse_known_args()
filepath = args.filename
filename = os.path.basename(filepath)
threshold = args.threshold
clean = args.clean

if not args.noseq:
    try:
        f = filename[:-4].split('-')
        if len(f) == 2:
            filename = f[0] + filename[-4:]
        if len(f) == 4:
            n = {i: j for i, j in zip(['row', 'column'], [int(i) for i in f[2:]])}
            filename = '-'.join(f[:2]) + filename[-4:]
        page = f[0].split('_').pop(-1)
    except ValueError:
        pass

fout = open('output/{}.jsonl'.format(filename[:-4]), 'w') 

if not os.path.isfile(filepath):
    r = {'ERROR': filepath, 'page': page, 'type': 'no such file'}
    json.dump(r, fout)
    fout.write('\n')    
    sys.exit(1)

def clean_image(this_grey):
    KERNEL = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    #KERNEL = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
    #KERNEL = cv2.getStructuringElement(cv2.MORPH_DIAMOND, (5, 5))
    out_grey = this_grey
    #out_grey = cv2.erode(out_grey, KERNEL, iterations = 1)
    #out_grey = cv2.dilate(out_grey, KERNEL, iterations = 1)
    #out_grey = cv2.morphologyEx(out_grey, cv2.MORPH_OPEN, KERNEL)
    out_grey = cv2.morphologyEx(out_grey, cv2.MORPH_CLOSE, KERNEL)
    return out_grey

def all_contours(img):
    cannied = cv2.Canny(img, threshold1=50, threshold2=200, apertureSize=7)
    return cv2.findContours(cannied, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)

def get_cut(img, p1, p2):
    return img[p1[1]:p2[1], p1[0]:p2[0]]

def get_rectangles(this_image, wmin=32, hmin=32):
    contours, _ = all_contours(this_image)
    r = []
    for (i, contour) in enumerate(contours):
        (x, y, w, h) = cv2.boundingRect(contour)
        if w > wmin and h > hmin:
            r.append([x, y, x + w, y + h, w, h])
    rectangles = pd.DataFrame(r, columns=['x1', 'y1', 'x2', 'y2', 'w', 'h'])
    rectangles = rectangles.drop_duplicates()
    rectangles = rectangles.sort_values(['x1', 'y1', 'x2', 'y2'])
    return rectangles.reset_index(drop=True)

def outer_rectangle(this_image):
    contours, _ = all_contours(this_image)
    (s, t) = grey.shape
    c_idx = []
    for (i, contour) in enumerate(contours):
        (x, y, w, h) = cv2.boundingRect(contour)
        if h > 0.5 * s  and w > 0.5 * t:
            c_idx.append(i)
    if not c_idx:
        r = {'ERROR': filepath, 'page': page, 'type': 'no bounding box'}
        json.dump(r, fout)
        fout.write('\n')
        sys.exit(1)
    return cv2.boundingRect(contours[c_idx[-1]])

def outer_p():
    def _p0():
        return cycle((i + 1) // 3 for i in range(4))
    def _p1():
        p1, p2 = tee(_p0())
        next(p2)
        return cycle(zip(p1, p2))
    q1, q2 = tee(_p1())
    next(q2)
    return ((i, j) if j > i else (j, i) for (i, j) in islice(zip(q1, q2), 4))

def outer_lines(x1, y1, x2, y2):
    def _points():
        return cycle(zip((x1, x2, x2, x1), (y1, y1, y2, y2)))
    q1, q2 = tee(_points())
    next(q2)
    return ((i, j) if j > i else (j, i) for (i, j) in islice(zip(q1, q2), 4))

def all_rectangles(this_image):
    rectangles = get_rectangles(this_image, hmin=38)
    r = []
    for (i, rectangle) in rectangles.iterrows():
        r.append(np.array([j for j in outer_lines(*rectangle[['x1', 'y1', 'x2', 'y2']])]))
    df1 = pd.DataFrame(np.array(r).reshape(-1, 4),
                       columns=['x1', 'y1', 'x2', 'y2'])
    df1['w'] = df1['x2'] - df1['x1']
    df1['h'] = df1['y2'] - df1['y1']
    return df1

def get_mode(this_series):
    return sorted(this_series)[this_series.shape[0] // 2]

def pairwise(iterable):
    i, j = tee(iterable)
    next(j, None)
    return zip(i, j)

def get_lines(this_grey):
    this_data = all_lines(this_grey, l=512)
    lines = pd.DataFrame(this_data, columns=['x1', 'y2', 'x2', 'y1'])
    outer_iter = outer_lines(x0, y0, x0 + w0, y0 + h0)
    outer = pd.DataFrame([i + j for (i, j) in outer_iter],
                         columns=['x1', 'y1', 'x2', 'y2'])
    lines = lines.append(outer, sort=True)
    lines = lines[['x1', 'y1', 'x2', 'y2']]
    lines = lines.sort_values(['x1', 'y1', 'x2', 'y2']).reset_index(drop=True)
    lines['w'] = lines['x2'] - lines['x1']
    lines['h'] = lines['y2'] - lines['y1']
    return lines

def get_horizontal(this_df):
    horizontal = this_df.sort_values('y1', ascending=False)
    horizontal['c'] = pd.cut(horizontal['y1'], 32, labels=range(32))
    horizontal = horizontal.drop_duplicates('c')
    horizontal = horizontal.sort_values('y1').reset_index(drop=True)
    horizontal['x1'] = get_mode(horizontal['x1'])
    horizontal['x2'] = get_mode(horizontal['x2'])
    return horizontal

def get_vertical2(this_df):
    vertical = this_df.sort_values('h', ascending=False)
    vertical['c'] = pd.cut(vertical['x1'], 16, labels=range(16))
    vertical = vertical.drop_duplicates('c')
    vertical = vertical.sort_index().reset_index(drop=True)
    vertical['d'] = pd.cut(vertical['y1'], 2, labels=range(2))
    return vertical

def get_vertical(this_df):
    vertical = this_df.sort_values('x1', ascending=False)
    vertical['c'] = pd.cut(vertical['x1'], 16, labels=range(16))
    vertical = vertical.drop_duplicates('c')
    vertical = vertical.sort_values('x1').reset_index(drop=True)
    vertical['d'] = pd.cut(vertical['y1'], 2, labels=range(2))
    return vertical

def horizontal_iter(horizontal):
    df1 = horizontal.shift(1).dropna().astype(int).reset_index(drop=True)
    df1 = df1.drop(['x2', 'y2', 'c', 'h', 'w'], axis=1)
    df2 = horizontal.shift(-1).dropna().astype(int).reset_index(drop=True)
    df2 = df2.drop(['x1', 'y1', 'c', 'h', 'w'], axis=1)
    df1 = df1.join(df2)
    return df1.iterrows()

def pad_image(this_grey, n):
    PADDING = (16, 26, 32, 32)
    this_grey = cv2.copyMakeBorder(this_grey, *PADDING,
                                   cv2.BORDER_CONSTANT, value=WHITE)
    outpath = 'work/{}-{}.png'.format(filename[:-4], str(n).zfill(4))
    cv2.imwrite(outpath, this_grey)
    return this_grey

def get_data(this_grey, config=''):
    ocrtext = tsrt.image_to_data(this_grey,
                                 config=config,
                                 output_type=tsrt.Output.DATAFRAME)
    text = ocrtext.dropna()
    if not text['text'].any():
        return text
    try:
        text['text'] = text['text'].astype(int).astype(str)
    except ValueError:
        pass
    idx1 = text[text['text'].str.strip() == ''].index
    text = text.drop(idx1)
    #idx2 = text[(text['height'] < 14) | (text['height'] > 38)].index
    #text = text.drop(idx2)
    idx3 = text[text['conf'] <= 1].index
    text = text.drop(idx3)
    text = text.rename(columns={'left': 'x1', 'top': 'y1',
                                'width': 'w', 'height': 'h'})
    return text


img = cv2.imread(filepath)
grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, grey = cv2.threshold(grey, 64, 255, cv2.THRESH_BINARY)

(x0, y0, w0, h0) = outer_rectangle(grey)
if args.rotate and h0 > w0:
    #print('rotate')
    grey = cv2.rotate(grey, cv2.ROTATE_90_CLOCKWISE)
    (x0, y0, w0, h0) = outer_rectangle(grey)

LINES = get_lines(grey)
HORIZONTAL = get_horizontal(LINES[LINES['w'] > 0.9 * w0].copy())
VERTICAL = get_vertical(LINES[LINES['h'] > 0.9 * h0].copy())

RECTANGLES = pd.DataFrame()
MCUT = np.diff(VERTICAL['x1'])[0]
for (i, s) in horizontal_iter(HORIZONTAL):
    if i < 2:
        vcut = VERTICAL.loc[VERTICAL['d'] == 0, 'x1']
    else:
        vcut = VERTICAL['x1'].drop(1)
    s['y1'] -= 3
    for (m, n) in pairwise(vcut):
        m -= 2
        n += 3
        s[['x1', 'x2']] = [m, n]
        RECTANGLES = RECTANGLES.append(s).astype(int)

RECTANGLES = RECTANGLES.reset_index(drop=True)
#print(filename)

grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
(x0, y0, w0, h0) = outer_rectangle(grey)
if args.rotate and h0 > w0:
    grey = cv2.rotate(grey, cv2.ROTATE_90_CLOCKWISE)
    (x0, y0, w0, h0) = outer_rectangle(grey)

if clean:
    grey = clean_image(grey)
_, grey = cv2.threshold(grey, threshold, 255, cv2.THRESH_BINARY)

#cv2.imwrite('grey.png', grey)

TEXT = {}
SECTIONS = {0: 'H01', 1: 'H02', 2: 'line_data', 3: 'route_data',
            4: 'H_Locations', 5: 'H_Lines', 6: 'H_Remarks',
            7: 'location_data', 8: 'graphic_data', 9: 'remarks_data'}

def get_textdict(text):
    text_block = text.groupby(['block_num', 'par_num',
                               'line_num', 'mblock'])
    return {j: {'text': ' '.join(text.iloc[k]['text'].values),
                'c': int(np.mean(text.iloc[k]['conf'].values) + 0.5)}
            for j, k in text_block.indices.items()}

for (i, s) in RECTANGLES.iterrows():
    t = s[['x1', 'y1', 'x2', 'y2']].values.reshape(-1, 2)
    grey_rectangle = get_cut(grey, *t)
    if i == 9:
        t0 = RECTANGLES.loc[7, ['x1', 'y1', 'x2', 'y2']].values.reshape(-1, 2)
        t0[1, 0] = MCUT + t0[0, 0]
        grey_rectangle = cv2.hconcat([get_cut(grey, *t0), grey_rectangle])
    if grey_rectangle.any():
        grey_rectangle = pad_image(grey_rectangle, i)
        if i in [7, 8, 9]:
            text = get_data(grey_rectangle, config='--psm 6')
            if text.empty:
                text = get_data(grey_rectangle)
        else:
            text = get_data(grey_rectangle)
        if text.empty:
            continue        
        text['text'] = text['text'].str.encode('ascii', 'replace')
        text['text'] = text['text'].str.decode('utf8')
        text['mblock'] = 0
        text.loc[(text['x1'] > MCUT) & (i == 7), 'mblock'] = 1
        text.loc[(text['x1'] > MCUT) & (i == 9), 'mblock'] = 3
        key = SECTIONS[i]
        if key == 'graphic_data':
            idx1 = text[~((text['conf'] > 85) & (text['h'] < 28) & (text['w'] > 28))].index
            text['mblock'] = 2
            text = text.drop(index=idx1)
        print('\t'.join([filepath, key, str(np.round(np.mean(text['conf']), 1))]))
        text_block = text.groupby(['block_num', 'par_num',
                                   'line_num', 'mblock'])
        TEXT[key] = ({j: ' '.join(text.iloc[k]['text'].values)
                      for j, k in text_block.indices.items()})

def fix_line_data(this_data):
    this_data = this_data.replace('|', '').replace(']', '').replace('  ', ' ')
    this_data = this_data.strip().split(' ')
    this_data[2] = ' '.join(this_data[2:-1])
    this_data[3] = this_data[-1]
    return this_data[:4]

def fix_route_data(this_data):
    this_data = this_data.replace('|', '').replace(']', '').replace('  ', ' ')
    this_data = this_data.strip().split(' ')
    if len(this_data) == 1:
        return [''] + this_data
    this_data[0] = ' '.join(this_data[:-1])
    this_data[1] = this_data[-1]
    return this_data[:2]

if 'line_data' not in TEXT:
    r = {'ERROR': filename, 'page': page, 'type': 'no line data'}
    json.dump(r, fout)
    fout.write('\n')
    sys.exit(1)

line_data = list(TEXT['line_data'].values())
if (1, 1, 1, 0) in TEXT['line_data']:
    line_data = fix_line_data(line_data[0])

route_data = list(TEXT['route_data'].values())
if (1, 1, 1, 0) in TEXT['route_data'] or len(route_data) == 1:
    route_data = fix_route_data(route_data[0])

r = {'LOR': line_data[0], '#': line_data[1], 'Description': line_data[-2], 'ELR': line_data[-1], 'Route': route_data[0], 'Date': route_data[1], 'page': page}

FIELD = {0: 'location', 1: 'offset', 2: 'text', 3: 'remark'}

for this_key, field in (('location_data', 'locations'), ('graphic_data', 'graphic_data'), ('remarks_data', 'remarks')):
    s = []
    if this_key not in TEXT:
        continue
    for i in [{'key': key[:3], FIELD[key[3]]: value} for key, value in TEXT[this_key].items()]:
        i['key'] = '{}:{}:{}'.format(*i['key'])
        k = i['key']
        if s and k == s[-1]['key']:
            s[-1] = {**s[-1], **i}
            continue
        s.append(i)
    r[field] = s

json.dump(r, fout)
fout.write('\n')
