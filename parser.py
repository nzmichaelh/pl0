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
        print('{}: Took {}'.format(stack, token))

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
        print('{}{}: {}'.format('  ' * indent, name, self))
        for name, child in self.children.items():
            if child and isinstance(child, Node):
                child.dump(name, indent + 1)
            else:
                print('{}{}: {}'.format('  ' * (indent + 1), name, child))


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
        self.set('ident', ident)
        self.set('expr', expr)


class Call(Statement):
    def __init__(self, ident):
        super().__init__()
        self.ident = ident


class Write(Statement):
    def __init__(self, expression):
        super().__init__()
        self.expression = expression


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
    factor = parse_factor(stream)
    term.append(factor)
    while stream.accept('*', '/'):
        term.append(stream.prev(), parse_factor(stream))
    return term


def parse_expression(stream):
    expression = Expression()
    expression.set('unary', stream.accept('+', '-'))
    expression.append(parse_term(stream))
    while stream.accept('+', '-'):
        expression.append(stream.prev())
        expression.append(parse_term(stream))
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
