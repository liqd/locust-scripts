VIRTUAL_ENV ?= .env

install:
	if [ ! -f $(VIRTUAL_ENV)/bin/python3 ]; then python3 -m venv .; fi
	$(VIRTUAL_ENV)/bin/python3 -m pip install --upgrade -r requirements.txt

run_ae:
	$(VIRTUAL_ENV)/bin/locust \
    --locustfile scripts/ae.py \
    --host https://ae-dev.liqd.net
