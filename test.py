#!/usr/bin/python
# Copyright (c) 2014 Alexander Sosedkin <monk@unboiled.info>, see LICENSE file

from trapl import trapl_eval

TESTS = (
    ('Hello_world!', 'Hello_world!'),
    ('Hello_world! len', 12),
    ('Hello_world! len str rev', '21'),
    ('trapl int new 100 neg', -100),
    ('trapl int new ( Hello_world! len str rev ) dec', 20),
    ('trapl int new 1 add ( trapl int new 2 ) inc', 4),
    ('trapl int new ( trapl str new 14 ) dec', 13),
    ('trapl with hi hello  hi', 'hello'),
    ('trapl with 3 ( trapl int new 4 )  3 add 3', 8),
    ('trapl expr  x ( a  b  c ) y  z', 'x ( a b c ) y z'),
    ('trapl str new ( trapl expr a ( b c ) d ) rev', 'd ) c b ( a'),
    ('trapl with s abc  trapl eval ( trapl expr s rev )', 'cba'),
    ('trapl with s abc  trapl with s Z  trapl eval ( trapl expr s )', 'abc'),
    ('trapl with X s  trapl with X abc  trapl eval ( trapl expr s )', 'abc'),
)

if __name__ == '__main__':
    for code, result in TESTS: assert trapl_eval(code) == result
