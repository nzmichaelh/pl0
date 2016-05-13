typedef int int_t;

void push(int_t v);
int_t pop();
void write(int_t v);
void run();

void ldci(int_t val);
void ldl(const int_t* p);
void stl(int_t* p);
void cup(void (*func)());
void csp(void (*func)(int_t v));

void adi();
void sbi();
void mpi();
void dvi();
void leqi();
void geqi();
void gti();
void lti();
void neqi();

void odd();

#define LABEL(_x) _x:
#define FJP(_x) if (!pop()) goto _x
#define UJP(_x) goto _x
