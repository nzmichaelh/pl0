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
"""Three address intermediate representation."""

import sys
from typing import Union
import typecheck as tc

from . import lex
from . import parser
from . import util


class Operand(util.ReprMixin):
    def lvalue(self):
        return self.rvalue()

    def rvalue(self):
        raise NotImplementedError()


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
    __slots__ = 'text', 'indent'

    def __init__(self, text, indent):
        self.text = text
        self.indent = indent


class Emittable(util.ReprMixin):
    pass


class Operation(Emittable):
    __slots__ = 'result', 'left', 'operation', 'right'

    @tc.typecheck
    def __init__(self,
                 result: Operand,
                 left: Operand,
                 operation: str,
                 right=None):
        self.result = result
        self.left = left
        self.operation = operation
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


class Enter(Emittable):
    __slots__ = ()


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


class Variables(util.Node):
    pass


class Constants(util.Node):
    pass


class Block(util.Node):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.vars_ = Variables()
        self.consts = Constants()
        self.operations = []


class Program(util.Node):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.blocks = []
        

class IRGenerator:
    def __init__(self):
        self.idx = 0
        self.program = None
        self.blocks = []
        self.indent = 0
        self.proc = None

    def next_id(self):
        self.idx += 1
        return self.idx

    def next_intermediate(self):
        operand = Intermediate(self.next_id())
        self.blocks[-1].vars_.append(operand)
        return operand

    def emit_program(self, program):
        self.program = Program(program)
        self.start_program(program)
        self.dispatch_children(program)
        self.end_program(program)
        return self.program

    def emit_block(self, block):
        b = Block(self.proc.name if self.proc else None)
        self.blocks.append(b)
        self.enter_block(block)
        result = self.dispatch_children(block)
        self.exit_block(block)
        self.blocks.pop()
        self.program.blocks.append(b)
        return result

    def emit_procedures(self, node):
        return self.dispatch_children(node)

    def emit_compound(self, node):
        return self.dispatch_children(node)

    def emit_procedure(self, proc):
        self.proc = proc
        return self.dispatch_children(proc)

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
            return None
        target = 'emit_{}'.format(node.typename())
        self.note('Invoking {}({})'.format(target, node))
        self.indent += 1
        result = getattr(self, target)(node)
        self.indent -= 1
        return result

    @tc.typecheck
    def header(self, msg: str):
        self.blocks[-1].operations.append(msg)

    @tc.typecheck
    def cmd(self, operation: Emittable):
        self.blocks[-1].operations.append(operation)

    @tc.typecheck
    def note(self, msg: str):
        if self.blocks and False:
            self.blocks[-1].operations.append(Note(msg, self.indent))

    def start_program(self, program):
        pass

    def end_program(self, program):
        pass

    def emit_body(self, statement):
        self.cmd(Enter('run'))
        self.dispatch(statement)
        self.cmd(Exit())

    def emit_vars(self, variables):
        for var in variables:
            self.blocks[-1].vars_.append(Variable(var.val))

    def emit_consts(self, consts):
        for name, val in consts.items():
            self.blocks[-1].consts.append(Const(name.val, val.val))

    def enter_block(self, block):
        self.cmd(Enter())

    def exit_block(self, block):
        self.cmd(Exit())

    def emit_call(self, node):
        self.cmd(Call(node.ident.val))

    def emit_assign(self, assign):
        operand = self.dispatch(assign.expr)
        self.cmd(Assign(Variable(assign.ident.val), operand, '='))

    def emit_number(self, token):
        return Number(token.val)

    def emit_ident(self, token):
        return Variable(token.val)

    def emit_write(self, node):
        operand = self.dispatch(node.expression)
        self.cmd(Call('write', operand.rvalue()))

    def emit_while(self, node):
        idx = self.next_id()

        top = Label('while{}'.format(idx))
        end = Label('while{}end'.format(idx))

        self.cmd(top)
        operand = self.dispatch(node.condition)
        self.cmd(If(operand.rvalue(), end))
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
    for operation in gen.operations:
        print('// {}'.format(operation))


def main():
    program = parser.parse(lex.lex(sys.stdin.read()))
    ir(program)


if __name__ == '__main__':
    main()
