#!/usr/bin/python
# Copyright (c) 2014 Alexander Sosedkin <monk@unboiled.info>, see LICENSE file

from trapl import trapl_eval, syntax_rich

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
    ('trapl code  x ( a  b  c ) y  z', 'x ( a b c ) y z'),
    ('trapl str new ( trapl code a ( b c ) d ) rev', 'd ) c b ( a'),
    ('trapl with s abc  trapl eval ( trapl code s rev )', 'cba'),
    ('trapl with s abc  trapl with s Z  trapl eval ( trapl code s )', 'abc'),
    ('trapl with X s  trapl with X abc  trapl eval ( trapl code s )', 'abc'),
    ('trapl with hello ( trapl ext hello shorten hi )  hello shorten', 'hi'),
    # Rich syntax examples
    ('@hello (trapl ext hello shorten hi)  hello shorten', 'hi'),
    ('@x abc  @x 100500  @x xoth  x', 'abc'),
    ("'Hello world!'", 'Hello world!'),
    ("trapl 'int' 'new' '4' 'inc' 'inc'", 6),
    (r"'\'Hello \\ \' world!\'\\'", "'Hello \\ ' world!'\\"),
    ("@s abc  @s Z  trapl eval ( trapl code s )", 'abc'),
    ("@ 's' abc  @ 's' Z  trapl eval ( trapl code s )", 'Z'),
    ('@mint (trapl ext (trapl int) _get_ (trapl ign))  mint new 4 x', 'x'),
    ('@mstr (trapl ext (trapl str) _get_ (pre cat))  mstr new Z 7', 'pre7'),
    ("@ '4+' (trapl int new 4 add) @ '7' (trapl int new 7)  4+ 7", 11),
    ("@mint (trapl atch (trapl int) 'ig' (trapl ign))  mint new 4 ig ig", 4),
    ("@mstr (trapl atch '' 'n' (trapl dtch 'smth' new))  mstr n Z", 'Z'),
    ("@ 'x' trapl.int  @ 'x' x.inc  @ 'x' x.inc.inc  x", 3),
    ("x = 'abc'  x = 'zte'  x", 'zte'),
    ("f = (trapl func x (trapl code 'hello' cat x rev))  f 'me'", 'emolleh'),
    ("f = {x|'hello' cat x rev}  f 'me'", 'emolleh'),
    ("f = {x|{z|x cat z cat x}}  f who let", 'wholetwho'),
    ("f = {x z|x cat z cat x}  f who let", 'wholetwho'),
    ("backapply = {x z|z x}  backapply int trapl", 0),
    ("backapply={ x z | z x }  backapply int trapl", 0),
)

if __name__ == '__main__':
    for code, result in TESTS:
        assert trapl_eval(code, syntax=syntax_rich) == result
