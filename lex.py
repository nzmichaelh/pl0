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

    while stream:
        ch = stream.read()
        if ch.isspace():
            if ch == '\n':
                line += 1
        elif ch.isalpha():
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


if __name__ == '__main__':
    for token in lex(sys.stdin.read()):
        print(token)
