from . import lex
from . import parser

import sys


class Emitter:
    def __init__(self):
        self.idx = 0

    def next_id(self):
        self.idx += 10
        return self.idx

    def emit_program(self, program):
        self.note('Program {}'.format(program))
        self.start_program(program)
        self.dispatch(program.block.consts)
        self.dispatch(program.block.vars)
        self.dispatch(program.block.procedures)
        self.emit_body(program.block.statement)

    def emit_block(self, block):
        self.dispatch_children(block)

    def emit_procedures(self, node):
        self.dispatch_children(node)

    def emit_compound(self, node):
        self.dispatch_children(node)

    def emit_procedure(self, proc):
        self.enter_procedure(proc)
        self.dispatch_children(proc)
        self.exit_procedure(proc)

    def emit_expression(self, expression):
        for term in expression.terms.children.values():
            self.dispatch(term)
        for operation in expression.operations.children.values():
            self.dispatch_operation(operation)

    def emit_term(self, term):
        for factor in term.factors.children.values():
            self.dispatch(factor)
        for operation in term.operations.children.values():
            self.dispatch_operation(operation)

    def emit_condition(self, cond):
        self.dispatch(cond.left)
        self.dispatch(cond.right)
        self.dispatch_operation(cond.code)

    def dispatch_children(self, node):
        for child in node.children.values():
            if isinstance(child, parser.Node):
                self.dispatch(child)

    def dispatch(self, node):
        if node is None:
            self.note('Skipping None')
            return
        target = 'emit_{}'.format(node.typename())
        self.note('Invoking {}({})'.format(target, node))
        getattr(self, target)(node)

    def dispatch_operation(self, op):
        self.note('Performing {}'.format(op))
        name = op.val
        if name == '#':
            name = '!='

        self.emit2(name)


class CEmitter(Emitter):
    def cmd(self, msg):
        print(msg)

    def note(self, msg):
        print('    // {}'.format(msg))

    def start_program(self, program):
        self.cmd('#include "pl0.h"')

    def emit_body(self, statement):
        self.cmd('void run() {')
        self.dispatch(statement)
        self.cmd('}')

    def emit_vars(self, vars):
        for var in vars:
            self.cmd('int_t {};'.format(var.val))

    def emit_consts(self, vars):
        for name, val in vars.items():
            self.cmd('const int_t {} = {};'.format(name.val, val.val))

    def enter_procedure(self, proc):
        self.cmd('void {}() {{'.format(proc.name))

    def exit_procedure(self, proc):
        self.cmd('}')

    def emit_call(self, node):
        self.cmd('{}();'.format(node.ident.val))

    def emit_assign(self, assign):
        self.dispatch(assign.expr)
        self.cmd('{} = pop();'.format(assign.ident.val))

    def emit_number(self, token):
        self.cmd('push({});'.format(token.val))

    def emit_ident(self, token):
        self.cmd('push({});'.format(token.val))

    def emit2(self, cmd):
        self.cmd(
            '{{ int_t right = pop(); int_t left = pop(); push(left {} right); }}'.format(
                cmd))

    def emit_write(self, node):
        self.dispatch(node.expression)
        self.cmd('write(pop());')

    def emit_while(self, node):
        idx = self.next_id()
        self.cmd('while{}:'.format(idx))
        self.dispatch(node.condition)
        self.cmd('if (!pop()) goto while{}end;'.format(idx))
        self.dispatch(node.statement)
        self.cmd('goto while{};'.format(idx))
        self.cmd('while{}end: ;'.format(idx))

    def emit_if(self, node):
        idx = self.next_id()
        self.dispatch(node.condition)
        self.cmd('if (!pop()) goto if{};'.format(idx))
        self.dispatch(node.statement)
        self.cmd('if{}: ;'.format(idx))

    def emit_odd(self, node):
        self.dispatch(node.expression)
        self.cmd('push(pop() & 1);')


class PMachineEmitter(Emitter):
    def cmd(self, msg):
        print(msg)

    def note(self, msg):
        print('    // {}'.format(msg))

    def start_program(self, program):
        self.cmd('#include "pl0.h"')

    def emit_body(self, statement):
        self.cmd('void run() {')
        self.dispatch(statement)
        self.cmd('}')

    def emit_vars(self, vars):
        for var in vars:
            self.cmd('int_t {};'.format(var.val))

    def emit_consts(self, vars):
        for name, val in vars.items():
            self.cmd('const int_t {} = {};'.format(name.val, val.val))

    def enter_procedure(self, proc):
        self.cmd('void {}() {{'.format(proc.name))

    def exit_procedure(self, proc):
        self.cmd('}')

    def emit_call(self, node):
        self.cmd('cup({});'.format(node.ident.val))

    def emit_assign(self, assign):
        self.dispatch(assign.expr)
        self.cmd('stl(&{});'.format(assign.ident.val))

    def emit_number(self, token):
        self.cmd('ldci({});'.format(token.val))

    def emit_ident(self, token):
        self.cmd('ldl(&{});'.format(token.val))

    def emit2(self, cmd):
        REMAP = {
            '+': 'adi',
            '-': 'sbi',
            '*': 'mpi',
            '/': 'dvi',
            '<=': 'leqi',
            '>=': 'geqi',
            '>': 'gti',
            '<': 'lti',
            '!=': 'neqi',
        }
        self.cmd('{}();'.format(REMAP[cmd]))

    def emit_write(self, node):
        self.dispatch(node.expression)
        self.cmd('csp(write);')

    def emit_while(self, node):
        idx = self.next_id()
        self.cmd('LABEL(while{});'.format(idx))
        self.dispatch(node.condition)
        self.cmd('FJP(while{}end);'.format(idx))
        self.dispatch(node.statement)
        self.cmd('UJP(while{});'.format(idx))
        self.cmd('LABEL(while{}end);'.format(idx))

    def emit_if(self, node):
        idx = self.next_id()
        self.dispatch(node.condition)
        self.cmd('FJP(if{});'.format(idx))
        self.dispatch(node.statement)
        self.cmd('LABEL(if{});'.format(idx))

    def emit_odd(self, node):
        self.dispatch(node.expression)
        self.cmd('odd();')


def emit(program):
    program.dump('top')
    emitter = PMachineEmitter()
    emitter.dispatch(program)


if __name__ == '__main__':
    program = parser.parse(lex.lex(sys.stdin.read()))
    emit(program)
