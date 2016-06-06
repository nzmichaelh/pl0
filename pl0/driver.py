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
import io
import sys

from . import lex
from . import parser
from . import ir
from . import codegen_riscv
from . import util

from cement.core.foundation import CementApp
from cement.core.controller import CementBaseController, expose


class Controller(CementBaseController):
    class Meta:
        label = 'base'

        arguments = [
            (['-o'], dict(action='store',
                          help='output filename')),
            (['src'], dict(action='store', nargs='*')),
        ]

    @expose(hide=True)
    def default(self):
        out = ''

        if not self.app.pargs.src:
            out = self.gen(sys.stdin.read())
        else:
            for src in self.app.pargs.src:
                with open(src, 'r') as f:
                    out += self.gen(f.read())

        if self.app.pargs.o:
            with open(self.app.pargs.o, 'w') as f:
                f.write(out)
        else:
            sys.stdout.write(out)

    def gen(self, src):
        tokens = lex.lex(src)
        ast = parser.parse(tokens)
        irf = ir.IRGenerator().dispatch(ast)
        sink = io.StringIO()
        gen = codegen_riscv.RISCVGenerator(sink).dispatch(irf)
        return sink.getvalue()


class Driver(CementApp):
    class Meta:
        label = 'pl0c'
        base_controller = Controller


def main():
    with Driver() as app:
        app.run()


if __name__ == '__main__':
    main()
