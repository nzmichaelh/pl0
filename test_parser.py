from . import parser, lex

TEST1 = """
const foo = 5, baz = 6;
var dog, cat;
procedure main;
begin
dog := 7;
call subproc;
! dog
end;
.
"""

SQUARES = """
VAR x, squ;

PROCEDURE square;
BEGIN
   squ:= x * x
END;

BEGIN
   x := 1;
   WHILE x <= 10 DO
   BEGIN
      CALL square;
      ! squ;
      x := x + 1
   END
END.
"""

MULDIV = """
CONST
  m =  7,
  n = 85;

VAR
  x, y, z, q, r;

PROCEDURE multiply;
VAR a, b;

BEGIN
  a := x;
  b := y;
  z := 0;
  WHILE b > 0 DO BEGIN
    IF ODD b THEN z := z + a;
    a := 2 * a;
    b := b / 2
  END
END;

PROCEDURE divide;
VAR w;
BEGIN
  r := x;
  q := 0;
  w := y;
  WHILE w <= r DO w := 2 * w;
  WHILE w > y DO BEGIN
    q := 2 * q;
    w := w / 2;
    IF w <= r THEN BEGIN
      r := r - w;
      q := q + 1
    END
  END
END;

PROCEDURE gcd;
VAR f, g;
BEGIN
  f := x;
  g := y;
  WHILE f # g DO BEGIN
    IF f < g THEN g := g - f;
    IF g < f THEN f := f - g
  END;
  z := f
END;

BEGIN
  x := m;
  y := n;
  CALL multiply;
  x := 25;
  y :=  3;
  CALL divide;
  x := 84;
  y := 36;
  CALL gcd
END.
"""

COMPOUND = """
VAR y;
BEGIN
y := 1+2*5;
y := 2*5+1;
END.
"""


def run(src):
    p = parser.parse(lex.lex(src))
    p.dump('top')
    return p


def test():
    assert run(TEST1) != None


def test_squares():
    assert run(SQUARES) != None


def test_muldiv():
    assert run(MULDIV) != None


def test_compound():
    assert run(COMPOUND) != None
