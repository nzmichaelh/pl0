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
        stack = ': '.join(reversed(names))
        print('{}: Took {}'.format(stack, token))

    def advance(self):
        self.at += 1

    def peek(self, offset):
        return self.tokens[self.at + offset]

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

    def append(self, value):
        self.set('_{}'.format(len(self.children)), value)

    def dump(self, name='', indent=0):
        print('{}{}: {}'.format('  ' * indent, name, self))
        for name, child in self.children.items():
            if isinstance(child, str) or child is None:
                print('{}{}: {}'.format('  ' * (indent + 1), name, child))
            else:
                child.dump(name, indent + 1)


class Consts(Node, dict):
    pass


class Vars(Node, dict):
    pass


class Block(Node):
    pass


class Statement(Node):
    pass


class Assign(Statement):
    def __init__(self, ident, expr):
        super().__init__()
        self.ident = ident
        self.expr = expr

    def __repr__(self):
        return '<Assign {} := {}>'.format(self.ident, self.expr)


class Call(Statement):
    def __init__(self, ident):
        super().__init__()
        self.ident = ident


class Write(Statement):
    def __init__(self, expression):
        super().__init__()
        self.expression = expression


class Procedures(Node):
    pass


class Procedure(Node):
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
    parse_expression(stream)
    stream.expect(')')


def parse_term(stream):
    factor = parse_factor(stream)
    while stream.accept('*', '/'):
        parse_factor(stream)


def parse_expression(stream):
    unary = stream.accept('+', '-')
    term = parse_term(stream)
    while stream.accept('+', '-'):
        parse_term(stream)


def parse_compound(stream):
    statements = [parse_statement(stream)]
    while stream.accept(';'):
        statements.append(parse_statement(stream))
    stream.expect('end')

    return Compound(statements)


def parse_condition(stream):
    if stream.accept('odd'):
        return parse_expression(stream)
    parse_expression(stream)
    stream.expect(lex.Token)
    parse_expression(stream)


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
        parse_condition(stream)
        stream.expect('then')
        return parse_statement(stream)
    if stream.accept('while'):
        parse_condition(stream)
        stream.expect('do')
        return parse_statement(stream)
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
    if stream.accept('var'):
        block.set('vars', parse_vars(stream))
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
    b = parse_block(stream)
    stream.expect('.')
    return b


if __name__ == '__main__':
    b = parse(lex.lex(sys.stdin.read()))
    b.dump('top')
