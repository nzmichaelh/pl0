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
from . import parser
from . import util

import sys
import typecheck as tc
from typing import Union


class Operand(util.ReprMixin):
    def lvalue(self):
        return self.rvalue()


class Number(Operand):
    __slots__ = 'val',

    def __init__(self, val):
        self.val = val

    def rvalue(self):
        return self.val


class Intermediate(Operand):
    __slots__ = 'idx',

    def __init__(self, idx):
        self.idx = idx

    def rvalue(self):
        return 't{}'.format(self.idx)


class Variable(Operand):
    __slots__ = 'val',

    def __init__(self, val):
        self.val = val

    def rvalue(self):
        return self.val


class Note(util.ReprMixin):
    __slots__ = 'text',

    def __init__(self, text):
        self.text = text


class Emittable(util.ReprMixin):
    pass


class Operation(Emittable):
    __slots__ = 'result', 'left', 'op', 'right'

    @tc.typecheck
    def __init__(self, result: Operand, left: Operand, op: str, right=None):
        self.result = result
        self.left = left
        self.op = op
        self.right = right


class TwoAddress(Operation):
    pass


class Condition(Operation):
    pass


class Branch(Emittable):
    pass


class Assign(TwoAddress):
    pass


class SingleValueEmittable(Emittable):
    __slots__ = 'val',

    def __init__(self, val):
        self.val = val


class Header(SingleValueEmittable):
    pass


class Reserve(SingleValueEmittable):
    pass


class Call(Emittable):
    __slots__ = 'name', 'arg'

    def __init__(self, name, arg=None):
        self.name = name
        self.arg = arg


class Label(SingleValueEmittable):
    pass


class Enter(SingleValueEmittable):
    pass


class Exit(Emittable):
    __slots__ = ()


class Const(Emittable):
    __slots__ = 'name', 'val'

    def __init__(self, name, val):
        self.name = name
        self.val = val


class If(Emittable):
    __slots__ = 'left', 'target'

    def __init__(self, left, target):
        self.left = left
        self.target = target


class Goto(SingleValueEmittable):
    pass


class Program:
    def __init__(self, name):
        self.name = name
        self.operations = []


class IRGenerator:
    def __init__(self):
        self.idx = 0
        self.program = None

    def next_id(self):
        self.idx += 1
        return self.idx

    def next_intermediate(self):
        op = Intermediate(self.next_id())
        self.cmd(Reserve(op.rvalue()))
        return op

    def emit_program(self, program):
        self.program = Program(program)
        self.start_program(program)
        self.dispatch(program.block.consts)
        self.dispatch(program.block.vars)
        self.dispatch(program.block.procedures)
        self.emit_body(program.block.statement)
        return self.program

    def emit_block(self, block):
        return self.dispatch_children(block)

    def emit_procedures(self, node):
        return self.dispatch_children(node)

    def emit_compound(self, node):
        return self.dispatch_children(node)

    def emit_procedure(self, proc):
        self.enter_procedure(proc)
        proc = self.dispatch_children(proc)
        self.exit_procedure(proc)

    def emit_expression(self, expression):
        terms = [self.dispatch(x) for x in expression.terms.children.values()]
        operations = list(expression.operations.children.values())

        for operation in operations:
            left, right = terms[0], terms[1]
            result = self.next_intermediate()
            self.cmd(Operation(result, left, operation.val, right))
            terms = [result] + terms[2:]
        assert len(terms) == 1
        return terms[0]

    def emit_term(self, term):
        factors = [self.dispatch(x) for x in term.factors.children.values()]
        operations = list(term.operations.children.values())
        cmds = []

        for operation in operations:
            left, right = factors[0], factors[1]
            result = self.next_intermediate()
            self.cmd(Operation(result, left, operation.val, right))
            factors = [result] + factors[2:]
        assert len(factors) == 1
        return factors[0]

    def emit_condition(self, cond):
        left = self.dispatch(cond.left)
        right = self.dispatch(cond.right)

        name = cond.code.val
        if name == '#':
            name = '!='

        result = self.next_intermediate()
        self.cmd(Condition(result, left, name, right))
        return result

    def dispatch_children(self, node):
        for child in node.children.values():
            if isinstance(child, parser.Node):
                self.dispatch(child)

    @tc.typecheck
    def dispatch(self, node) -> Union[Operation, Variable, Intermediate,
                                      Number, Program, None]:
        if node is None:
            self.note('Skipping None')
            return None
        target = 'emit_{}'.format(node.typename())
        self.note('Invoking {}({})'.format(target, node))
        return getattr(self, target)(node)

    @tc.typecheck
    def header(self, msg: str):
        self.program.operations.append(msg)

    @tc.typecheck
    def cmd(self, operation: Emittable):
        self.program.operations.append(operation)

    @tc.typecheck
    def note(self, msg: str):
        if self.program:
            self.program.operations.append(Note(msg))

    def start_program(self, program):
        pass

    def emit_body(self, statement):
        self.cmd(Enter('run'))
        self.dispatch(statement)
        self.cmd(Exit())

    def emit_vars(self, vars):
        for var in vars:
            self.cmd(Reserve(var.val))

    def emit_consts(self, vars):
        for name, val in vars.items():
            self.cmd(Const(name.val, val.val))

    def enter_procedure(self, proc):
        self.cmd(Enter(proc.name))

    def exit_procedure(self, proc):
        self.cmd(Exit())

    def emit_call(self, node):
        self.cmd(Call(node.ident.val))

    def emit_assign(self, assign):
        op = self.dispatch(assign.expr)
        self.cmd(Assign(Variable(assign.ident.val), op, '='))

    def emit_number(self, token):
        return Number(token.val)

    def emit_ident(self, token):
        return Variable(token.val)

    def emit_write(self, node):
        op = self.dispatch(node.expression)
        self.cmd(Call('write', op.rvalue()))

    def emit_while(self, node):
        idx = self.next_id()

        top = Label('while{}'.format(idx))
        end = Label('while{}end'.format(idx))

        self.cmd(top)
        op = self.dispatch(node.condition)
        self.cmd(If(op.rvalue(), end))
        self.dispatch(node.statement)
        self.cmd(Goto(top))
        self.cmd(end)

    def emit_if(self, node):
        idx = self.next_id()
        cond = self.dispatch(node.condition)

        target = Label('if{}'.format(idx))
        self.cmd(If(cond.rvalue(), target))
        self.dispatch(node.statement)
        self.cmd(target)

    def emit_odd(self, node):
        left = self.dispatch(node.expression)
        result = self.next_intermediate()
        self.cmd(Operation(result, left, '&', Number(1)))
        return result


def ir(program):
    program.dump('top')
    irgen = IRGenerator()
    gen = irgen.dispatch(program)

    print('// {}'.format(gen.name))
    for op in gen.operations:
        print(op)


if __name__ == '__main__':
    program = parser.parse(lex.lex(sys.stdin.read()))
    ir(program)
