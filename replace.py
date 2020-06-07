#!/usr/bin/env python

import os, sys, glob

replacements = (
    # ('╱', '/'),
    # ('╲', '\\'),
    # '╱ /',
    # '╲ \\',
    # '▞ \u2692',
    # '▚ \u2693',
    # '▧ \u2587',
    # '⌸ \u269a',
    # '⧚  \u2551',
    '🐘  \u26c8',
    '📚  \u26ac',
    '☃  \u2603',
    '❄  \u26a6',
    # '▐ \u25a4',
    # ('⋇', '*'),
    # '* ⋇',
    # '| ┇',

)

arg=sys.argv[1:][0]
count = 0
for fn in glob.glob(f'maps/{arg}.map'):
    with open(fn) as fp:
        txt = fp.read()
    for r in replacements:
        a,b=r.split()
        print("a", a)
        print("b", b)
        new = txt.replace(a,b)
        if new!=txt:
            count+=1
        txt = new
    with open(fn, 'w') as fp:
        fp.write(txt)

print(f'{count} replacements made')
