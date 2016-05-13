#include "pl0.h"

#include <cstdio>

static int_t stack[100];
static int at = 0;

void push(int_t v) {
    stack[++at] = v;
}

int_t pop() {
    return stack[at--];
}

void write(int_t v) {
    printf("%d\n", v);
}

void ldci(int_t val) {
    push(val);
}

void ldl(const int_t* p) {
    push(*p);
}

void stl(int_t* p) {
    *p = pop();
}

void cup(void (*func)()) {
    func();
}

void csp(void (*func)(int_t v)) {
    func(pop());
}

void odd() {
    push(pop() & 1);
}

#define OP(_n, _x) void _n() { int_t right = pop(); int_t left = pop(); push(left _x right); }

OP(adi, +);
OP(sbi, -);
OP(mpi, *);
OP(dvi, /);
OP(leqi, <=);
OP(geqi, >=);
OP(gti, >);
OP(lti, <);
OP(neqi, !=);


int main() {
    run();
    return 0;
}
