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
"""A code generator that emits C code."""

import sys

from . import lex
from . import parser
from . import ir
from . import util


class RISCVGenerator:
    def __init__(self):
        pass

    def dispatch(self, node):
        if isinstance(node, (list, tuple)):
            for item in node:
                self.dispatch(item)
        else:
            target = 'emit_{}'.format(util.typename(node))
            return getattr(self, target)(node)

    def emit_note(self, note):
        self.note(note.text, note.indent)

    def emit_program(self, program):
        self.cmd('#include "pl0.h"')
        main = program.blocks[-1]
        self.dispatch(main.vars_)
        self.dispatch(main.consts)
        for block in program.blocks:
            if block != main:
                self.dispatch(block)
        self.block = main
        self.dispatch(main.operations)

    def emit_variables(self, variables):
        for var in variables:
            if isinstance(var, ir.Variable):
                self.cmd('int_t {};'.format(var.val))

    def emit_constants(self, consts):
        for var in consts:
            self.cmd('const int_t {} = {};'.format(var.name, var.val))

    def emit_block(self, block):
        self.block = block
        self.dispatch(block.operations)

    def emit_reserve(self, reserve):
        self.cmd('int_t {};'.format(reserve.val))

    def emit_enter(self, enter):
        name = self.block.name or 'run'
        self.cmd('void {}() {{'.format(name))
        for var in self.block.vars_:
            if isinstance(var, ir.Intermediate):
                self.cmd('int_t t{};'.format(var.idx))
            elif self.block.name is not None:
                self.cmd('int_t {};'.format(var.val))

    def emit_assign(self, assign):
        self.cmd('{} = {};'.format(assign.result.lvalue(), assign.left.rvalue(
        )))

    def emit_exit(self, exit_):
        self.cmd('}')

    def emit_label(self, label):
        self.cmd('{}: ;'.format(label.val))

    def emit_const(self, const):
        self.cmd('const int_t {} = {};'.format(const.name, const.val))

    def emit_condition(self, cond):
        self.emit_operation(cond)

    def emit_if(self, ifcmd):
        self.cmd('if (!{}) goto {};'.format(ifcmd.left, ifcmd.target.val))

    def emit_goto(self, goto):
        self.cmd('goto {};'.format(goto.val.val))

    def emit_operation(self, operation):
        self.cmd('{} = {} {} {};'.format(operation.result.lvalue(
        ), operation.left.rvalue(), operation.operation,
                                         operation.right.rvalue()))

    def emit_call(self, call):
        if call.arg is not None:
            self.cmd('{}({});'.format(call.name, call.arg))
        else:
            self.cmd('{}();'.format(call.name))

    def cmd(self, msg: str):
        print(msg)

    def note(self, msg: str, indent=0):
        print('// {}{}'.format('  ' * indent, msg))


def codegen(program):
    irgen = ir.IRGenerator()
    irf = irgen.dispatch(program)
    irf.dump()
    cgen = RISCVGenerator()
    gen = cgen.dispatch(irf)


def main():
    program = parser.parse(lex.lex(sys.stdin.read()))
    codegen(program)


if __name__ == '__main__':
    main()
