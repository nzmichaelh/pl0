# PL/0 implementation

Idea: implement a PL/0 compiler and VM from scratch.

https://en.wikipedia.org/wiki/PL/0

Grammer is defined in EBNF.

* [foo] is optional, so foo must be present 0 or 1 times.
* {foo} is repeated 0 or more times.

## Language

The final top level block is equivalent to main().

## Recursive descent parser

A mechanical conversion from the BNF form to code.

- accept() checks if the next token is the starting one.
- expect() requires the next token is a certain one.

## Other implementations
https://github.com/crcx/PL0-Language-Tools

## Components

Tokeniser
Parser
Generator
