from . import lex


def run(src):
    return [x.val for x in lex.lex(src)]


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
