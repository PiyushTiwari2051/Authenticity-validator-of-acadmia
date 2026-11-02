# ==============================================================================
# Sanad Machine Learning Pipeline Makefile
# ==============================================================================

PYTHON ?= python

.PHONY: help data-fetch data-build data-check train-ocr train-extract train-tamper train-fusion eval report clean

help:
	@echo "Sanad ML Operational Commands:"
	@echo "  make data-fetch   - Fetch open datasets & output gated instructions"
	@echo "  make data-build   - Procedurally synthesize Sanad-Cert dataset (8 families, T1-T10)"
	@echo "  make data-check   - Run integrity, leakage, hash, and arithmetic tests"
	@echo "  make train-ocr    - Train / tune OCR recognizers (Tesseract/Paddle/docTR)"
	@echo "  make train-extract- Train key-field extraction models"
	@echo "  make train-tamper - Train tamper localization models (DTD / FPH / baseline)"
	@echo "  make train-fusion - Train decision fusion classifier on validation features"
	@echo "  make eval         - Run frozen test-split benchmarks and generate metrics"
	@echo "  make report       - Generate final consolidated markdown evaluation report"
	@echo "  make clean        - Remove cached temporary files and build artifacts"

data-fetch:
	$(PYTHON) -m ml.src.data.fetch

data-build:
	$(PYTHON) -m ml.src.data.build_sanad_cert

data-check:
	$(PYTHON) -m ml.src.data.check_data

train-ocr:
	$(PYTHON) -m ml.src.train.train_ocr

train-extract:
	$(PYTHON) -m ml.src.train.train_extract

train-tamper:
	$(PYTHON) -m ml.src.train.train_tamper

train-fusion:
	$(PYTHON) -m ml.src.train.train_fusion

eval:
	$(PYTHON) -m ml.src.eval.run_eval

report:
	$(PYTHON) -m ml.src.eval.generate_report

clean:
	$(PYTHON) -c "import shutil, os; [shutil.rmtree(p) for p in ['ml/__pycache__', 'ml/eval/__pycache__'] if os.path.exists(p)]"
