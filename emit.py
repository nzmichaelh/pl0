from . import lex
from . import parser


class Emitter:
    def __init__(self):
        pass

    def cmd(self, msg):
        print(msg)

    def emit_program(self, program):
        self.cmd('; Program {}'.format(program))
        self.dispatch_children(program)

    def emit_block(self, block):
        self.dispatch_children(block)

    def emit_vars(self, vars):
        pass

    def emit_consts(self, vars):
        pass

    def emit_procedures(self, vars):
        self.dispatch_children(vars)

    def emit_compound(self, vars):
        self.dispatch_children(vars)

    def emit_assign(self, assign):
        self.dispatch(assign.expr)
        self.cmd('{} = pop'.format(assign.ident.val))

    def emit_expression(self, expression):
        for term in expression.terms.children.values():
            self.dispatch(term)
        for operation in expression.operations.children.values():
            self.cmd('do {}'.format(operation.val))

    def emit_term(self, term):
        for factor in term.factors.children.values():
            self.dispatch(factor)
        for operation in term.operations.children.values():
            self.cmd('do {}'.format(operation.val))

    def emit_number(self, token):
        self.cmd('push #{}'.format(token.val))

    def emit_ident(self, token):
        self.cmd('load {}'.format(token.val))

    def dispatch_children(self, node):
        for child in node.children.values():
            if isinstance(child, parser.Node):
                self.dispatch(child)

    def dispatch(self, node):
        if node is None:
            self.cmd('; Skipping None')
            return
        target = 'emit_{}'.format(node.typename())
        print('; invoking {}({})'.format(target, node))
        getattr(self, target)(node)


def emit(program):
    program.dump('top')
    emitter = Emitter()
    emitter.dispatch(program)


if __name__ == '__main__':
    program = parse(lex.lex(sys.stdin.read()))
    emit(b)
