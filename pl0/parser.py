# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from . import lex

import collections
import sys
import inspect


class TokenStream:
    def __init__(self, tokens):
        self.tokens = tokens
        self.at = -1

    def log(self, token):
        calls = inspect.stack()
        context = calls[0][1]
        names = []
        for call in calls:
            if call[1] == context:
                name = call[3]
                if name.startswith('parse_'):
                    name = name[6:]
                names.append(name)
            else:
                break
        stack = ': '.join(reversed(names[1:]))
        #print('{}: Took {}'.format(stack, token))

    def advance(self):
        self.at += 1

    def peek(self, offset):
        return self.tokens[self.at + offset]

    def prev(self):
        return self.tokens[self.at - 1]

    def accept(self, *vals, nolog=False):
        token = self.tokens[self.at]
        for val in vals:
            if isinstance(val, str):
                match = (token.val == val)
            else:
                match = isinstance(token, val)

            if match:
                self.advance()
                if not nolog:
                    self.log(token)
                return token
        else:
            return None

    def expect(self, *vals):
        tokens = []

        for val in vals:
            token = self.accept(val, nolog=True)
            if not token:
                assert False, 'Parse error: expected {}, got {}'.format(
                    repr(val), self.tokens[self.at])
            tokens.append(token)
            self.log(token)
        if len(tokens) == 1:
            return tokens[0]
        else:
            return tokens


class Node:
    def __init__(self):
        self.children = collections.OrderedDict()

    def set(self, name, value):
        setattr(self, name, value)
        self.children[name] = value

    def append(self, *vals):
        for value in vals:
            self.set('_{}'.format(len(self.children)), value)

    def dump(self, name='', indent=0):
        print('// {}{}: {}'.format('  ' * indent, name, self))
        for name, child in self.children.items():
            if child and isinstance(child, Node):
                child.dump(name, indent + 1)
            else:
                pass
                print('// {}{}: {}'.format('  ' * (indent + 1), name, child))

    def typename(self):
        return self.__class__.__name__.lower()


class Consts(Node, dict):
    pass


class Vars(Node, dict):
    pass


class List(Node):
    def __init__(self, items):
        super().__init__()
        for item in items:
            self.append(item)


class Block(Node):
    pass


class Program(Node):
    def __init__(self, block):
        super().__init__()
        self.set('block', block)


class Statement(Node):
    pass


class Assign(Statement):
    def __init__(self, ident, expr):
        super().__init__()
        self.set('ident', ident)
        self.set('expr', expr)


class Call(Statement):
    def __init__(self, ident):
        super().__init__()
        self.set('ident', ident)


class Write(Statement):
    def __init__(self, expression):
        super().__init__()
        self.set('expression', expression)


class While(Statement):
    def __init__(self, condition, statement):
        super().__init__()
        self.set('condition', condition)
        self.set('statement', statement)


class If(Statement):
    def __init__(self, condition, statement):
        super().__init__()
        self.set('condition', condition)
        self.set('statement', statement)


class Odd(Node):
    def __init__(self, expression):
        super().__init__()
        self.set('expression', expression)


class Condition(Node):
    def __init__(self, left, code, right):
        super().__init__()
        self.set('left', left)
        self.set('code', code)
        self.set('right', right)


class Procedures(Node):
    pass


class Procedure(Node):
    pass


class Expression(Node):
    pass


class Term(Node):
    pass


def parse_consts(stream):
    consts = Consts()
    name, _, value = stream.expect(lex.Ident, '=', lex.Number)
    consts[name] = value

    while stream.accept(','):
        name, _, value = stream.expect(lex.Ident, '=', lex.Number)
        consts[name] = value

    stream.expect(';')
    return consts


def parse_vars(stream):
    vars = Vars()
    name = stream.expect(lex.Ident)
    vars[name] = True

    while stream.accept(','):
        name = stream.expect(lex.Ident)
        vars[name] = True
    stream.expect(';')
    return vars


class Compound(Statement):
    def __init__(self, statements):
        super().__init__()
        for statement in statements:
            self.append(statement)


def parse_factor(stream):
    term = stream.accept(lex.Ident, lex.Number)
    if term:
        return term
    stream.expect('(')
    expression = parse_expression(stream)
    stream.expect(')')
    return expression


def parse_term(stream):
    term = Term()
    factors, operations = [], []
    factors.append(parse_factor(stream))
    while stream.accept('*', '/'):
        operations.append(stream.prev())
        factors.append(parse_factor(stream))
    term.set('factors', List(factors))
    term.set('operations', List(operations))
    return term


def parse_expression(stream):
    expression = Expression()
    expression.set('unary', stream.accept('+', '-'))
    terms, operations = [], []
    terms.append(parse_term(stream))
    while stream.accept('+', '-'):
        operations.append(stream.prev())
        terms.append(parse_term(stream))
    expression.set('terms', List(terms))
    expression.set('operations', List(operations))
    return expression


def parse_compound(stream):
    statements = [parse_statement(stream)]
    while stream.accept(';'):
        statements.append(parse_statement(stream))
    stream.expect('end')

    return Compound(statements)


def parse_condition(stream):
    if stream.accept('odd'):
        return Odd(parse_expression(stream))
    return Condition(
        parse_expression(stream), stream.expect(lex.Token),
        parse_expression(stream))


def parse_statement(stream):
    if stream.accept(lex.Ident):
        stream.expect(':=')
        return Assign(stream.peek(-2), parse_expression(stream))
    if stream.accept('call'):
        return Call(stream.expect(lex.Ident))
    if stream.accept('!'):
        return Write(parse_expression(stream))
    if stream.accept('begin'):
        return parse_compound(stream)
    if stream.accept('if'):
        cond, _, statement = parse_condition(stream), stream.expect(
            'then'), parse_statement(stream)
        return If(cond, statement)
    if stream.accept('while'):
        cond, _, statement = parse_condition(stream), stream.expect(
            'do'), parse_statement(stream)
        return While(cond, statement)
    return None


def parse_procedure(stream):
    procedure = Procedure()
    name, _ = stream.expect(lex.Ident, ';')
    block = parse_block(stream)
    stream.expect(';')
    procedure.set('name', name.val)
    procedure.set('block', block)
    return procedure


def parse_block(stream):
    block = Block()

    if stream.accept('const'):
        block.set('consts', parse_consts(stream))
    else:
        block.set('consts', Consts())

    if stream.accept('var'):
        block.set('vars', parse_vars(stream))
    else:
        block.set('vars', Vars())

    procedures = Procedures()
    while stream.accept('procedure'):
        procedure = parse_procedure(stream)
        procedures.set(procedure.name, procedure)
    block.set('procedures', procedures)
    block.set('statement', parse_statement(stream))

    return block


def parse(tokens):
    stream = TokenStream(list(tokens))

    stream.advance()
    block, _ = parse_block(stream), stream.expect('.')
    return Program(block)


if __name__ == '__main__':
    b = parse(lex.lex(sys.stdin.read()))
    b.dump('top')
