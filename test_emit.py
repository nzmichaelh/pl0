from . import emit
from . import lex
from . import parser

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
    emit.emit(parser.parse(lex.lex(src)))
    return True


def test_compound():
    assert run(COMPOUND) != None
