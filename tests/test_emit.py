import pl0.emit
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
    pl0.emit.emit(pl0.parser.parse(pl0.lex.lex(src)))
    return True


def test_compound():
    assert run(COMPOUND) != None
