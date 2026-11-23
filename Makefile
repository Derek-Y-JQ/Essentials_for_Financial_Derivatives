.PHONY: pdf web all clean

PDF_OUT := Essentials_for_Financial_Derivatives.pdf

all: pdf web

pdf:
	mkdir -p build
	xelatex -interaction=nonstopmode -output-directory=build main.tex
	xelatex -interaction=nonstopmode -output-directory=build main.tex
	cp build/main.pdf $(PDF_OUT)
	mkdir -p docs
	cp build/main.pdf docs/$(PDF_OUT)

web:
	python3 scripts/build_web.py

clean:
	rm -rf build
