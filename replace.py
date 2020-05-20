#!/usr/bin/env python

import os, sys, glob

replacements = (
    # ('╱', '/'),
    '/ ╱',
    # ('╲', '\\'),
    '\\ ╲',
    # ('⋇', '*'),
    '* ⋇',
    '| ┇',

)

for fn in glob.glob('maps/5.map'):
    with open(fn) as fp:
        txt = fp.read()
    for r in replacements:
        a,b=r.split()
        txt = txt.replace(a,b)
    with open(fn, 'w') as fp:
        fp.write(txt)
