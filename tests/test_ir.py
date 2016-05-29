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
import pl0.ir
import pl0.lex
import pl0.parser

COMPOUND = """
CONST z = 10;
VAR y;
BEGIN
y := 1+2*5;
y := 2*5+1;
y := (1+2)*5*z;
END.
"""


def run(src):
    pl0.ir.ir(pl0.parser.parse(pl0.lex.lex(src)))
    return True


def test_compound():
    assert run(COMPOUND) != None
