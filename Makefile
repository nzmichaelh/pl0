%.cc: %.pl0
	python3 -m pl0.emit < $< | $@
