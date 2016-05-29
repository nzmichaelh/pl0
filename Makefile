SRC = $(wildcard examples/*.pl0)
CXXSRC = $(SRC:%.pl0=%.cc)
BIN = $(SRC:%.pl0=%)

CXXFLAGS = -Ilib -g -Og

all: $(BIN)

run: $(BIN:%=%-run)

cxx: $(CXXSRC)

%-run: %
	$<

%.cc: %.pl0 $(wildcard *.py) Makefile
	python3 -m pl0.codegen_c < $< > $@

%: %.cc $(wildcard lib/*)
	$(CXX) $(CXXFLAGS) -o $@ $< lib/pl0.cc

clean:
	rm -rf $(BIN) $(CXXSRC)
