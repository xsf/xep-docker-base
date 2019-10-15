all: quick.pdf

quick.pdf: quick.tex
	pdflatex $<

pyfiles := $(wildcard ../../../bin/*py) ../../../scripts/texml_local

quick.tex: quick.texml $(pyfiles)
	../../../scripts/texml_local --width 60 $< $@

quick.texml: quick.xsl quick.html
	xsltproc -o $@ $+

clean:
	rm -f *log *aux *~
