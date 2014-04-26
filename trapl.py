#!/usr/bin/python
# Toy Reduced Awful Programming Language
# Copyright (c) 2014 Alexander Sosedkin <monk@unboiled.info>, see LICENSE file

import re, base64

class TRAPLError(RuntimeError): pass

class mydict(dict):
    def __getattr__(self, k):    return self[k]
    def __setitem__(self, k, v): raise TRAPLError('__setitem__ disabled')
    def __setattr__(self, k, v): raise TRAPLError('__setattr__ disabled')
    def clear(self, *a, **kwar): raise TRAPLError('clear disabled')
    def update(self, *a, **kwa): raise TRAPLError('update disabled')
    def setdefault(s, *a, **kw): raise TRAPLError('setdefault disabled')
    def __call__(self, *a, **k):
        n = self.copy()
        n.update(dict(*a, **k))
        return mydict(n)

BASE_OBJ = mydict()
TRAPL = BASE_OBJ({
    'obj': BASE_OBJ,
    'int': BASE_OBJ({
        '_val_': 0,
        'new': BASE_OBJ(_meth_=lambda i: BASE_OBJ(_call_=lambda s:
            i(_val_=int(s._val_))
        )),
        'neg': BASE_OBJ(_meth_=lambda i: i(_val_=-i._val_)),
        'inc': BASE_OBJ(_meth_=lambda i: i(_val_=(i._val_ + 1))),
        'dec': BASE_OBJ(_meth_=lambda i: i(_val_=(i._val_ - 1))),
        'add': BASE_OBJ(_meth_=lambda a: BASE_OBJ(_call_=lambda b:
            a(_val_=a._val_ + b._val_)
        )),
        'str': BASE_OBJ(_meth_=lambda a: TRAPL['str'](_val_=str(a._val_))),
    }),
    'str': BASE_OBJ({
        '_val_': '',
        'new': BASE_OBJ(_meth_=lambda s: BASE_OBJ(_call_=lambda n:
            s(_val_=n._val_),
        )),
        'cat': BASE_OBJ(_meth_=lambda s: BASE_OBJ(_call_=lambda n:
            s(_val_=(s._val_ + n._val_))
        )),
        'len': BASE_OBJ(_meth_=lambda s: TRAPL['int'](_val_=len(s._val_))),
        'rev': BASE_OBJ(_meth_=lambda s: s(_val_=s._val_[::-1])),
        'dec': BASE_OBJ(_meth_=lambda s: BASE_OBJ(_call_=lambda e:
            s(_val_=decode_str(e._val_))
        )),
    }),
    'ign': BASE_OBJ(_call_=lambda x: x),
    'skip': BASE_OBJ(_call_=lambda x: BASE_OBJ(_call_=lambda y: x)),
    'ext': BASE_OBJ(_call_=lambda o: BASE_OBJ(_call_=lambda name:
            BASE_OBJ(_call_=lambda ext: o({name._val_: ext})
    ))),
    'code': BASE_OBJ(_magic_='code'),
    'eval': BASE_OBJ(_call_=lambda code: BASE_OBJ(
        _magic_='eval', _magic_code_=code,
    )),
    'with': BASE_OBJ(_call_=lambda name: BASE_OBJ(_call_=lambda val: BASE_OBJ(
        _magic_='with', _magic_name_=name._val_, _magic_value_=val,
    ))),
    'func': BASE_OBJ(_call_=lambda arg_name: BASE_OBJ(_call_=lambda code:
        BASE_OBJ(
            code=code,
            _call_=lambda arg_val: BASE_OBJ(
                _magic_='eval', _magic_code_=code,
                _magic_context_={arg_name._val_: arg_val}
    )))),
    'atch': BASE_OBJ(_call_=lambda o: BASE_OBJ(_call_=lambda name:
        BASE_OBJ(_call_=lambda call:
            o({name._val_: BASE_OBJ(_meth_=call._call_)})
    ))),
    'dtch': BASE_OBJ(_call_=lambda o: BASE_OBJ(_call_=lambda name:
        BASE_OBJ(_call_=o[name._val_]._meth_)
    )),
})

def parse(tokens):
    tree = []
    while tokens:
        t = tokens.pop(0)
        if t == '(': tree.append(parse(tokens))
        elif t == ')': return tree
        else: tree.append(t)
    return tree

flatten = lambda t: \
    ' '.join('( ' + flatten(a) + ' )' if isinstance(a, list) else a for a in t)

def trapl_apply(to, what):
    if '_call_' in to: return to._call_(what)
    if not '_val_' in what: raise TRAPLError('No _val_ in %s' % what)
    if what._val_ in to:
        x = to[what._val_]
    # TODO LATER: Implement this functionality in trapl, remove from here
    elif '_get_' in to:
        x = trapl_apply(trapl_apply(to, TRAPL['str'](_val_='_get_')), what)
    else:
        raise TRAPLError('No %s in %s' % (what._val_, to.keys()))
    if '_meth_' in x: return x._meth_(to)
    return x

def _trapl_eval(tree, context=None):
    context = {'trapl': TRAPL} if context is None else context.copy()
    curr = None
    while tree:
        next = tree.pop(0)
        if isinstance(next, list): next = _trapl_eval(next, context)
        if isinstance(next, str):
            next = context.get(next, TRAPL['str'](_val_=next))
        curr = trapl_apply(curr, next) if not curr is None else next
        if '_magic_' in curr:
            if curr._magic_ == 'with':
                context[curr._magic_name_] = curr._magic_value_
                curr = TRAPL['ign']
            elif curr._magic_ == 'eval':
                utree = parse(curr._magic_code_._val_.split())
                ctx = context
                if '_magic_context_' in curr: ctx.update(curr._magic_context_)
                curr = _trapl_eval(utree, ctx)
            elif curr._magic_ == 'code':
                # TODO: fall out of current brace if empty (allows trapl.code)
                to_the_end, tree = tree, []
                curr = TRAPL['str'](_val_=flatten(to_the_end))
    return curr or BASE_OBJ

syntax_plain = lambda code: code
def trapl_eval(code, syntax=syntax_plain):
    return _trapl_eval(parse(syntax(code).split()))['_val_']

encode_str = lambda s: 'ENC' + base64.b32encode(s).replace('=', '0')
decode_str = lambda s: base64.b32decode(s[3:].replace('0', '='))
include_str = lambda s: ' ( trapl str dec %s ) ' % encode_str(s)
quotes = lambda code: re.sub(r"\B'([^'\\]*(?:\\.[^'\\]*)*)'\B", lambda m:
    include_str(m.group(1).replace('\\\'', '\'').replace('\\\\', '\\')), code)
dots = lambda code: re.sub(r"(\w*(?:\.(?:\w*))+)", lambda m:
    ' ( ' + m.group(1).split('.')[0] + ' ' +
    ' '.join(include_str(s) for s in m.group(1).split('.')[1:]) + ' ) ', code)
assign = lambda code: re.sub(r"(\w*)(?:\s*)=", lambda m:
    'trapl with %s ' % include_str(m.group(1)), code)

def syntax_rich(code):
    code = quotes(code)
    code = dots(code)
    code = assign(code)
    for o, s in {'(': ' ( ', ')': ' ) ', '@': 'trapl with '}.items():
        code = code.replace(o, s)
    return code

if __name__ == '__main__':
    import sys
    for f in [file(fname) for fname in sys.argv[1:]] or [sys.stdin]:
        print trapl_eval(f.read(), syntax=syntax_rich)
