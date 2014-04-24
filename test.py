#!/usr/bin/python
# Copyright (c) 2014 Alexander Sosedkin <monk@unboiled.info>, see LICENSE file

from trapl import trapl_eval

TESTS = (
    ('trapl int new 1 add ( trapl int new 2 ) inc', 4),
    ('trapl int new ( trapl str new 14 ) dec', 13),
    ('trapl with hi hello  hi', 'hello'),
    ('trapl with 3 ( trapl int new 4 )  3 add 3', 8),
    ('trapl expr  x ( a  b  c ) y  z', 'x ( a b c ) y z'),
    ('trapl str new ( trapl expr a ( b c ) d ) rev', 'd ) c b ( a'),
    ('trapl with s abc  trapl eval ( trapl expr s rev )', 'cba'),
)

if __name__ == '__main__':
    for code, result in TESTS: assert trapl_eval(code) == result
