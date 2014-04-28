#!/usr/bin/python
# Copyright (c) 2014 Alexander Sosedkin <monk@unboiled.info>, see LICENSE file

from trapl import trapl_eval, syntax_rich, TRAPLError

import sys, time

TESTS_CORE_SYNTAX = (
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
    ('trapl false not', True),
    ('trapl false not and z', 'z'),
    ('trapl true not', False),
    ('trapl true not or z', 'z'),
    ('hello eq hello or z', True),
    ('3 eq 4 not and also', 'also'),
    ('trapl ign x', 'x'),
    ('trapl with sum ( trapl func a ( a cat 5 ) )  sum 4', 'a5'),
    ('trapl with sum ( trapl func a ( trapl code a cat 5 ) )  sum 4', '45'),
)

TESTS_RICH_SYNTAX = (
    ("'Hello world!'", 'Hello world!'),
    ("3 sub 5", -2),
    ("@hello (trapl ext hello shorten hi)  hello shorten", 'hi'),
    ("@x abc  @x 100500  @x xoth  x", 'abc'),
    ("trapl 'int' 'new' '4' 'inc' 'inc'", 6),
    (r"'\'Hello \\ \' world!\'\\'", "'Hello \\ ' world!'\\"),
    ("@s abc  @s Z  trapl eval ( trapl code s )", 'abc'),
    ("@ 's' abc  @ 's' Z  trapl eval ( trapl code s )", 'Z'),
    ("@mint (trapl ext (trapl int) _get_ (trapl ign))  mint new 4 x", 'x'),
    ("@mstr (trapl ext (trapl str) _get_ (pre cat))  mstr new Z '7'", 'pre7'),
    ("@ '4+' (4 add) @ '7' (7)  trapl get '4+' 7", 11),
    ("@mint (trapl atch (trapl int) 'ig' (trapl ign))  mint new 4 ig ig", 4),
    ("@mstr (trapl atch '' 'n' (trapl dtch 'smth' new))  mstr n Z", 'Z'),
    ("@ 'x' trapl.int  @ 'x' x.inc  @ 'x' x.inc.inc  x", 3),
    ("x = 'abc'  x = 'zte'  x", 'zte'),
    ("f = (trapl func x (trapl code 'hello' cat x rev))  f 'me'", 'emolleh'),
    ("f = {x|'hello' cat x rev}  f 'me'", 'emolleh'),
    ("{x|'hello' cat x rev} 'me'", 'emolleh'),
    ("f = {x|{z|x cat z cat x}}  f who let", 'wholetwho'),
    ("f = {x z|x cat z cat x}  f who let", 'wholetwho'),
    ("backapply = {x z|z x}  backapply int trapl", 0),
    ("backapply={ x z | z x }  backapply int trapl", 0),
    ("t=trapl.true  cmp={a b|a eq b}  cmp 3 4 not and (cmp t t)", True),
    ("t=trapl.true  neq={a b|a eq b not}  neq 3 4 and (neq t (t not))", True),
    ("match={a b|trapl.if (a eq b) 'yes' 'no' } match ('eh' rev) 'he'", 'yes'),
    ("match={a b|trapl.if (a eq b) 'yes' 'no' } match 'nei' 'he'", 'no'),
    ("fi = {c e t|trapl.if c t e}  fi trapl.true 'x' 'y'", 'y'),
    ("fi = {c e t|trapl.if c t e}  fi trapl.false 'x' 'y'", 'x'),
    ("sum = {a b|a cat b}  hll = (sum hel)  hll lo", 'hello'),
    ("s={a b|a cat b} (s (s h i) (s h i))", 'hihi'),
    ("pre = 'zz'  f = {x|pre cat x}  trapl.drop 'pre' f x", 'zzx'),
    ("bk = {x y|y x}  bk drop trapl 'bk'  bk", 'bk'),
    ("a = {x y|x add y}  f = {x|a x 1}  x = 9  f 6", 7),
    ("a = {x y|x add y}  f = {y|a y 1}  y = 9  f 6", 7),
    ("a = {x y|x add y}  f = {z y|a y 1}  y = 9  f 0 6", 7),
    ("a = {x y|x add y}  f = {x y|a y 1}  y = 9  f 0 6", 7),
    ("twisted = {f x y|f y x}  tst = (twisted '')  tst 'hello' cat", 'hello'),
    ("twisted = {f x y|f y x}  twisted Y Z cat", 'YZ'),
    ("twisted = {f x y|f y x}  postZ = {x|twisted x Z cat}  postZ Y", 'YZ'),
    ("t={f x y|f y x}  post={p x|t x p cat}  trapl.drop 't'  post Z Y", 'YZ'),
    ("t = {f x y|f y x}  s = {x f|x add (f neg)}  st = (t s)  st 3 4", 1),
    ("sub = { x y | x add (y neg) }  sub 3 (4 neg)", 7),
    ("y = 'a'  x = 'j'         f = { x | x cat y }  y = 'b'  f n", 'na'),
    ("y = 'a'                  f = { x | x cat y } trapl.drop 'y' f n", 'na'),
    ("y = 'a'                  f = { x | x cat y }  y = 'b'  f n", 'na'),
    ("                         f = { x | x cat y }  y = 'b'  f n", 'nb'),
    ("y = 'a'  f = (trapl drop 'y' { x | x cat y }) y = 'b'  f n", 'nb'),
    ("""
    f = {x|trapl.eval(trapl.if (x eq 0) (
       trapl.code 'x'
      ) (
       trapl.code (x str cat (f (x dec)))
    ))}
    f 3
    """, '321x'),
)

if __name__ == '__main__':
    #for t, s in ((TESTS_CORE_SYNTAX, None), (TESTS_RICH_SYNTAX, syntax_rich)):
    #    for code, result in t: assert trapl_eval(code, syntax=s) == result
    # The horror below is a prettier (in runtime) equivalent to the code above
    tests = [t + (None,) for t in TESTS_CORE_SYNTAX]
    tests += [t + (syntax_rich,) for t in TESTS_RICH_SYNTAX]
    e, n, status, report, times = 0, len(tests), '', '', []
    if len(sys.argv) > 1: repeat = int(sys.argv[1])
    repeat = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    for i, (code, result, syntax) in enumerate(tests):
        try:
            start = time.time()
            for j in range(repeat):
                r = trapl_eval(code, syntax=syntax)
            times.append((time.time() - start) * 1000 / repeat)
        except TRAPLError, ex:
            r = ex
        if r != result:
            e += 1
            report += 'code     %s\n' % code
            report += 'returned %s\nand not  %s\n' % (str(r)[:70], str(result))
        sys.stdout.write('\b' * len(status))
        l = int(60 * float(i + 1) / n)
        status = '.'*l + ' '*(60 - l) + ' %d/%d, %d errors' % (i + 1, n, e)
        sys.stdout.write(status); sys.stdout.flush()
    report = report or '%dms: avg %dms max %dms\n' % \
            (sum(times), sum(times)/n, max(times))
    sys.stdout.write('\n' + report)
