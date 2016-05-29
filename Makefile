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
SRC = $(wildcard examples/*.pl0)
CXXSRC = $(SRC:%.pl0=%.cc)
BIN = $(SRC:%.pl0=%)
CHECKS = $(wildcard tests/*.pl0)

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
	rm -rf $(BIN) $(CXXSRC) tests/*.elf tests/*.cc tests/*.out tests/*.checked

check: $(CHECKS:%.pl0=%.checked)

%.expect: %.pl0
	awk -F: '/# Expect:/ {print $$2}' $< | sed 's/^ *//' | tr ' ' '\n' > $@

%.checked: %.out %.expect
	diff -wu $< $*.expect

%.out: %.elf
	$< > $@

%.elf: %.cc
	$(CXX) $(CXXFLAGS) -o $@ $< lib/pl0.cc
