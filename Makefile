DOCS = wsgidispatcher.html wsgicollection.html

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
