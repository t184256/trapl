#!/usr/bin/python
# Toy Reduced Awful Programming Language
# Copyright (c) 2014 Alexander Sosedkin <monk@unboiled.info>, see LICENSE file

# This program is an interpreter for a toy language with simple syntax rules:
# (try reading the examples in test.py, most are pretty self-explanatory!)
# 1) Braces define priority
# 2) Applications chains: 'obj1 obj2 obj3' means obj3 gets applied to
#    the result of obj2 to obj1 application and so on
# Application usually means a dictionary lookup in first object,
# but there also are other important effects of application (see trapl_apply):
# 1) if first is a 'callable' it calls a wrapped python functions of 1 argument
# 2) if second is a 'method' it gets applied to the first object
# Additional syntax is supported with source-to-source transformations.
# The interpreter reuses python stack, closures... staying relatively compact.
# For even simpler, but less capable versions, please refer to the previous
# versions in the VCS (first version was very simple and < 87 lines long!).

class TRAPLError(RuntimeError): pass # a base exception for interpreter errors

class mydict(dict): # a lousily implemented immutable dictionary
    def __getattr__(self, k):    return self[k]
    def __setitem__(self, k, v): raise TRAPLError('__setitem__ disabled')
    def __setattr__(self, k, v): raise TRAPLError('__setattr__ disabled')
    def clear(self, *a, **kwar): raise TRAPLError('clear disabled')
    def update(self, *a, **kwa): raise TRAPLError('update disabled')
    def setdefault(s, *a, **kw): raise TRAPLError('setdefault disabled')
    def __call__(self, *a, **k): # this is how you extend mydict:
        n = self.copy()          # mydict({'a': 'b'})({'c': 'd'})(x='y')
        n.update(dict(*a, **k))  # results in a new mydict equivalent to
        return mydict(n)         # mydict({'a': 'b', 'c': 'd', 'x': 'y'})

OBJ = mydict() # create an immutable object, the base for all future objects
# methods and callables are objects with special fields (see trapl_apply)
METH = lambda body, **kwa: OBJ(_meth_=body, **kwa) # method and callables are
CALL = lambda body, **kwa: OBJ(_call_=body, **kwa) # created like this
# this is how you create a method of obj a that takes an additional parameter:
EQ = METH(lambda a: CALL(lambda b: # this means the method returns a callable
    TRAPL['true'] if a._val_ == b._val_ else TRAPL['false'] # which returns this
))
TRAPL = OBJ({ # let's define the standard library, accessible later as 'trapl'
    'obj': OBJ, # provide a means of accessing the original, blank object
    'false': OBJ({ # an instance of a boolean value false
        '_val_': False, # put a python-object value in _val_
        'not': METH(lambda b: b(_val_=(not b._val_))), # and several methods
        # understanding how they work remains as an exercise
        'or': METH(lambda b: CALL(lambda arg:
            arg if not b._val_ else b # this way 'false or 2' is 2
        )),
        'and': METH(lambda b: CALL(lambda arg:
            arg if b._val_ else b # this way 'true and 2' is 2
        )),
        'eq': EQ, # this is the example universal method from the above
    }),
    'int': OBJ({
        '_val_': 0,
        'new': METH(lambda i: CALL(lambda s: i(_val_=int(s._val_)))),
        'neg': METH(lambda i: i(_val_=-i._val_)),
        'inc': METH(lambda i: i(_val_=(i._val_ + 1))),
        'add': METH(lambda a: CALL(lambda b: a(_val_=a._val_ + b._val_))),
        'str': METH(lambda a: TRAPL['str'](_val_=str(a._val_))),
        'eq': EQ,
    }),
    'str': OBJ({
        '_val_': '',
        'new': METH(lambda s: CALL(lambda n: s(_val_=n._val_))),
        'cat': METH(lambda s: CALL(lambda n: s(_val_=(s._val_ + n._val_)))),
        'len': METH(lambda s: TRAPL['int'](_val_=len(s._val_))),
        'rev': METH(lambda s: s(_val_=s._val_[::-1])),
        'dec': METH(lambda s: CALL(lambda e: s(_val_=decode_str(e._val_)))),
        'eq': EQ,
    }),
    'ext': CALL(lambda o: CALL(lambda n: CALL(lambda w: o({n._val_: w})))),
    'code': OBJ(_magic_='code'), # objects with _magic_ are special
    'eval': CALL(lambda code: OBJ(_magic_='eval', _magic_code_=code)),
    'drop': CALL(lambda name: OBJ(_magic_='drop', _magic_name_=name._val_)),
    'with': CALL(lambda name: CALL(lambda val:
        OBJ(_magic_='with', _magic_name_=name._val_, _magic_value_=val)
    )), # injects {name._val_: val} in current context, see trapl_eval
    'get': CALL(lambda name: OBJ(_magic_='get', _magic_name_=name._val_)),
    'func': CALL(lambda arg_name: CALL(lambda code:
        OBJ(_magic_='func', _magic_code_=code, _magic_arg_name_=arg_name),
    )), # make a callable will evaluate code with {arg_name._val_: arg_val}
    'atch': CALL(lambda o: CALL(lambda name: CALL(lambda call:
            o({name._val_: METH(call._call_)})
    ))), # Attaches a callable call to an object o as amethod with name name
    'dtch': CALL(lambda o: CALL(lambda name:
        CALL(o[name._val_]._meth_)
    )), # Returns a method detached from an object and turned into a callable
    'if': CALL(lambda cond:
        CALL(lambda val_true: CALL(lambda unused_val_false: val_true))
        if cond._val_ == True else
        CALL(lambda unused_val_true: CALL(lambda val_false: val_false))
    ),
})

def parse(tokens): # turns 'a ( b ( c ) d )' into ['a', ['b', ['c'], 'd']]
    if isinstance(tokens, str): tokens = tokens.split()
    tree = []
    while tokens:
        t = tokens.pop(0)
        if t == '(': tree.append(parse(tokens))
        elif t == ')': break
        else: tree.append(t)
    return tree

# Does the reverse job
flatten = lambda t: \
    ' '.join('( ' + flatten(a) + ' )' if isinstance(a, list) else a for a in t)

def trapl_apply(to, what): # Handles how one object gets applied to another
    if '_call_' in to: return to._call_(what) # appying to a callable calls it
    if not '_val_' in what: raise TRAPLError('No _val_ in %s' % what)
    if what._val_ in to: # if it's a string mathcing one of the object's keys
        x = to[what._val_] # retrieve it from the object
    # TODO LATER: Implement this functionality in trapl, remove from here
    elif '_get_' in to: # otherwise call a special catchall callable if present
        x = trapl_apply(trapl_apply(to, TRAPL['str'](_val_='_get_')), what)
    else:
        raise TRAPLError('No %s in %s' % (what._val_, to.keys()))
    if '_meth_' in x: return x._meth_(to) # if the result is a method, apply it
    # Note: to get a method from the object without appying it, see dtach
    return x

def _trapl_eval(tree, context=None, default_object=OBJ): # evaluate a tree
    context = {'trapl': TRAPL} if context is None else context.copy()
    curr = None
    while tree:
        next, tree = tree[0], tree[1:]
        if isinstance(next, list): next = _trapl_eval(next, context)
        if isinstance(next, str): # Autocast unknown literals to strings
            next = context.get(next, TRAPL['str'](_val_=next))
        curr = trapl_apply(curr, next) if not curr is None else next
        while '_magic_' in curr: # Handle special messages to the interpreter
            if curr._magic_ == 'with': # inject a value in current context
                context[curr._magic_name_] = curr._magic_value_
                curr = TRAPL['ign']
            elif curr._magic_ == 'drop': # inject a value in current context
                del context[curr._magic_name_]
                curr = TRAPL['ign']
            elif curr._magic_ == 'get': # get a value from current context
                curr = context[curr._magic_name_] # see '4+' example in test.py
            elif curr._magic_ == 'eval': # evaluate a string
                utree = parse(curr._magic_code_._val_)
                ctx = context.copy()
                if '_magic_definition_context_' in curr:
                    ctx.update(curr._magic_definition_context_)
                if '_magic_arg_val_' in curr:
                    ctx[curr._magic_arg_name_._val_] = curr._magic_arg_val_
                curr = _trapl_eval(utree, ctx)
            elif curr._magic_ == 'func': # create a function (closure)
                ctx, arg_name = context.copy(), curr._magic_arg_name_
                code = curr._magic_code_
                curr = CALL(lambda arg_val:
                    OBJ(_magic_='eval',
                        _magic_code_=code,
                        _magic_arg_name_=arg_name,
                        _magic_arg_val_=arg_val,
                        _magic_definition_context_=context,
                ))
            elif curr._magic_ == 'code': # create a string from remaining code
                # fall out of current brace if empty (allows trapl.code)
                if not tree: return curr
                curr = TRAPL['str'](_val_=flatten(tree))
                tree = []
    return curr or default_object

syntax_plain = lambda code: code # source code transformations may be used
# Let's define some code transformations to make syntax more pleasant
import re, base64
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

curly_func = lambda code: flatten(_curly_func(parse(
    code.replace('{', ' ( { ').replace('}', ' } ) ').replace('|', ' | ')
)))
funcize = lambda argname, tree: \
    ['trapl', 'func', parse(include_str(argname)), ['trapl', 'code'] + tree]
def _curly_func(tree):
    if isinstance(tree, str): return tree
    if len(tree) > 3:
        if tree[0] == '{' and '|' in tree[1:-1] and tree[-1] == '}':
            i = tree[1:-1].index('|') + 1
            args, tree = tree[1:i], tree[i+1:-1]
            for a in args[::-1]:
                tree = funcize(a, tree)
    return [_curly_func(t) for t in tree]

autoint = lambda code: re.sub(r"\b(\d+)\b", lambda m:
    ' ( trapl int new ' + include_str(m.group(1)) + ' ) ', code)

def syntax_rich(code): # apply lots of source-to-source transformations
    # convert 'a' into ( trapl string dec ENCSMTH ) to protect it
    code = quotes(code) # from futher damage, respects escaping
    # convert {a b|b a} -> (trapl func a ( trapl code ( trapl func b (
    code = code.replace('(', ' ( ').replace(')', ' ) ') # HACK: deduplicate
    code = curly_func(code) # trapl code b a ) ) ) )
    code = autoint(code) # convert 3 -> ( trapl int new 3 )
    code = dots(code) # convert t = trapl.true -> t = (trapl true)
    code = assign(code) # convert t=(trapl true) -> trapl with t (trapl true)
    # puts spaces around braces so they become separate tokens
    for o, s in {'(': ' ( ', ')': ' ) ', '@': 'trapl with '}.items():
        code = code.replace(o, s) # also handles a tricky-to-use shortcut
    return code

def trapl_eval(code, syntax=None, unbox=True): # evaluate a string
    r = _trapl_eval(parse((syntax or syntax_plain)(code)))
    return r._val_ if unbox else r

# Now that we have a bare language to play with,
# let's use it to extend its standard library!
TRAPL = trapl_eval('trapl ext trapl true ( trapl false not )', unbox=False)
TRAPL = trapl_eval("""trapl.ext trapl 'int' (
  trapl.atch trapl.int 'dec' {x|x neg inc neg}
)""", syntax=syntax_rich, unbox=False)
treval = lambda code: trapl_eval(code, syntax=syntax_rich, unbox=False) # short
TRAPL = treval("trapl.ext trapl 'ign' {x|x}") # trapl.ign x -> x
TRAPL = treval("""trapl.ext trapl 'int' (
  trapl.atch trapl.int 'sub' {x y|x add (y neg)}
)""")

if __name__ == '__main__':
    import sys # evaluates a list of files or stdin contents
    for f in [file(fname) for fname in sys.argv[1:]] or [sys.stdin]:
        print trapl_eval(f.read(), syntax=syntax_rich)
