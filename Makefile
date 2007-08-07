DOCS = wsgidispatcher.html wsgicollection.html
PYTHONPATH=$(shell pwd)

default: doc test

.phony: test 
test:
	python runtests.py

.phony: doc
doc: $(DOCS)
%.html: %.py
	python2.5 extract_doc.py $<  > $@

clean:
	rm  $(DOCS)
