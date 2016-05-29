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
import pl0.lex


def run(src):
    return [x.val for x in pl0.lex.lex(src)]


def test():
    assert run('123') == [123]
    assert run('123 456') == [123, 456]
    assert run('<=') == ['<=']
    assert run('> 5') == ['>', 5]
    assert run('  baz bar  foo\n') == ['baz', 'bar', 'foo']


def test_comments():
    assert run('# Comment until EOL\n123') == [123]
    assert run('  # Space before comments\n123') == [123]
    assert run('# Comment on last line') == []
