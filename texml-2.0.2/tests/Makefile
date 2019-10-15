# $Id: Makefile,v 1.17 2006-07-20 03:41:23 olpa Exp $

all: tests

clean:
	rm -rf *~ */*~ tmp

good_xml_tests:=$(notdir $(wildcard data/*xml)) quick.xml
good_test_stamps=$(addprefix tmp/data/,$(good_xml_tests:.xml=.stamp))
fail_xml_tests:=$(notdir $(wildcard faildata/*xml))
fail_test_stamps=$(addprefix tmp/faildata/,$(fail_xml_tests:.xml=.stamp))

texml_modules:=$(wildcard ../Texml/*py)
texml_program_files=$(texml_modules) ../scripts/texml.py
texml_script=../scripts/texml_local

#
# Individual test parameters to converter
#
params-mixed      = -e ascii
params-koi8       = -e koi8-r
params-koi8_ns    = -e koi8-r
params-koi8bad    = -e koi8-r
params-koi8bad_ns = -e koi8-r
params-latex      = -e koi8-r
params-latex_ns   = -e koi8-r
params-cmdnest    = -e ascii
params-wselim2    = -w 100
params-wselim2_ns = -w 100
params-quick      = -w 60
params-quick_ns   = -w 60
params-context    = --context -e utf8
params-context_ns = --context -e utf8
params-chinese1   = -e utf8 -a
params-tour_pdfok = -e koi8-r
params-aenc       = --encoding utf8 -a

tests: $(good_test_stamps) $(fail_test_stamps)

#
# Initialization, creation of folders
#
init=tmp/data/.stamp tmp/faildata/.stamp

tmp/data/.stamp tmp/faildata/.stamp:
	mkdir -p $(dir $@)
	touch $@

# Need a line after "FORCE"
FORCE:

# Need a line after "FORCE"

.SECONDARY:

#
# Running "good" tests
#
tmp/data/%.out: data/%.xml $(texml_program_files) data/%.out $(init)
	$(texml_script) $(call params-$*) $< $@

tmp/data/%.stamp: tmp/data/%.out FORCE
	diff -qs $(basename $@).out data/$(notdir $*).out

#
# Running "bad" tests: if fact, we make grep of error message
#
tmp/faildata/%.err: faildata/%.xml $(texml_program_files) $(init)
	$(texml_script) $< $(basename $@).out 2>$@ || true

tmp/faildata/%.stamp: tmp/faildata/%.err FORCE
	grep -q -f faildata/$(notdir $*).grep $<

#
# Dependencies for quick start files
#
data/quick.xml: data/quick/quick.texml
	cp $< $@

data/quick.out: data/quick/quick.tex
	cp $< $@

