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

from . import lex
from . import parser
from . import ir
from . import util

import sys


class CGenerator:
    def __init__(self):
        pass

    def emit_program(self, program):
        self.cmd('#include "pl0.h"')
        self.note(program)
        self.dispatch(program.operations)

    def dispatch(self, node):
        if isinstance(node, list) or isinstance(node, tuple):
            for item in node:
                self.dispatch(item)
        else:
            target = 'emit_{}'.format(util.typename(node))
            self.note('Invoking {}({})'.format(target, node))
            return getattr(self, target)(node)

    def emit_note(self, note):
        self.note(note.text)

    def emit_reserve(self, reserve):
        self.cmd('int_t {};'.format(reserve.val))

    def emit_enter(self, enter):
        self.cmd('void {}() {{'.format(enter.val))

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

    def emit_operation(self, op):
        self.cmd('{} = {} {} {};'.format(op.result.lvalue(), op.left.rvalue(),
                                         op.op, op.right.rvalue()))

    def emit_call(self, call):
        if call.arg is not None:
            self.cmd('{}({});'.format(call.name, call.arg))
        else:
            self.cmd('{}();'.format(call.name))

    def cmd(self, msg: str):
        print(msg)

    def note(self, msg: str):
        print('// {}'.format(msg))


def codegen(program):
    program.dump('top')
    irgen = ir.IRGenerator()
    irf = irgen.dispatch(program)
    cgen = CGenerator()
    gen = cgen.dispatch(irf)


if __name__ == '__main__':
    program = parser.parse(lex.lex(sys.stdin.read()))
    codegen(program)
