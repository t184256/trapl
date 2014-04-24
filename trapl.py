#!/usr/bin/python
# Toy Reduced Awful Programming Language
# Copyright (c) 2014 Alexander Sosedkin <monk@unboiled.info>, see LICENSE file

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
    'ign': BASE_OBJ(_call_=lambda x: x),
    'int': BASE_OBJ({
        '_val_': 0,
        'new': BASE_OBJ(_call_=lambda s: TRAPL['int'](_val_=int(s._val_))),
        'neg': BASE_OBJ(_meth_=lambda i: TRAPL['int'](_val_=-i._val_)),
        'inc': BASE_OBJ(_meth_=lambda i: TRAPL['int'](_val_=i._val_ + 1)),
        'dec': BASE_OBJ(_meth_=lambda i: TRAPL['int'](_val_=i._val_ - 1)),
        'add': BASE_OBJ(_meth_=lambda a: BASE_OBJ(_call_=lambda b:
            TRAPL['int'](_val_=a._val_ + b._val_)
        )),
        'str': BASE_OBJ(_meth_=lambda a: TRAPL['str'](_val_=str(a._val_)))
    }),
    'eval': BASE_OBJ(_call_=lambda code: BASE_OBJ(
        _magic_='eval', _magic_code_=code,
    )),
    'code': BASE_OBJ(_magic_='code'),
    'with': BASE_OBJ(_call_=lambda name: BASE_OBJ(_call_=lambda val: BASE_OBJ(
        _magic_='with', _magic_name_=name._val_, _magic_value_=val,
    ))),
    'str': BASE_OBJ({
        '_val_': '',
        'new': BASE_OBJ(_call_=lambda s: TRAPL['str'](_val_=s._val_)),
        'rev': BASE_OBJ(_meth_=lambda s: TRAPL['str'](_val_=s._val_[::-1])),
        'len': BASE_OBJ(_meth_=lambda s: TRAPL['int'](_val_=len(s._val_))),
    }),
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
    x = to[what._val_]
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
                curr = _trapl_eval(utree, context)
            elif curr._magic_ == 'code':
                to_the_end, tree = tree, []
                curr = TRAPL['str'](_val_=flatten(to_the_end))
    return curr or BASE_OBJ

def trapl_eval(code): return _trapl_eval(parse(code.split()))['_val_']

if __name__ == '__main__': print trapl_eval(raw_input())
