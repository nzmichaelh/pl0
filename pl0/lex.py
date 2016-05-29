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
import sys

KEYWORDS = 'const var procedure call begin end if then while do odd'.lower(
).split()


class Token:
    def __init__(self, val, line):
        self.val = val
        self.line = line

    def __repr__(self):
        return '<{} {}:{}>'.format(self.__class__.__name__, repr(self.val),
                                   self.line)

    def typename(self):
        return self.__class__.__name__.lower()


class Ident(Token):
    pass


class Keyword(Token):
    pass


class Number(Token):
    pass


class PeekStream:
    def __init__(self, src):
        self.src = src
        self.at = -1

    def peek(self):
        idx = self.at + 1
        if idx >= len(self.src):
            return None
        else:
            return self.src[idx]

    def read(self):
        idx = self.at + 1
        if idx >= len(self.src):
            return None
        else:
            self.at = idx
            return self.src[idx]

    def __len__(self):
        return len(self.src) - self.at - 1


def accumulate(stream, first, cond):
    out = first

    while stream:
        ch = stream.peek()
        if not cond(ch):
            break
        out += stream.read()
    return out


def lex(src):
    stream = PeekStream(src)
    line = 1
    sol = True

    while stream:
        ch = stream.read()
        if ch.isspace():
            if ch == '\n':
                line += 1
                sol = True
        elif ch == '#' and sol:
            while stream.peek() not in ['\n', None]:
                stream.read()
        else:
            sol = False

            if ch.isalpha():
                token = accumulate(stream, ch, str.isalnum)
                if token.lower() in KEYWORDS:
                    yield Keyword(token.lower(), line)
                else:
                    yield Ident(token, line)
            elif ch.isdigit():
                yield Number(int(accumulate(stream, ch, str.isdigit)), line)
            elif ch in '<>' and stream.peek() == '=':
                yield Token(ch + stream.read(), line)
            elif ch == ':' and stream.peek() == '=':
                yield Token(ch + stream.read(), line)
            else:
                yield Token(ch, line)


def main():
    for token in lex(sys.stdin.read()):
        print(token)


if __name__ == '__main__':
    main()
