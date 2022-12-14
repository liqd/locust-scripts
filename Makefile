VIRTUAL_ENV ?= .venv

.PHONY: install
install:
	if [ ! -f $(VIRTUAL_ENV)/bin/python3 ]; then python3 -m venv $(VIRTUAL_ENV); fi
	$(VIRTUAL_ENV)/bin/python3 -m pip install --upgrade -r requirements.txt

.PHONY: berlin-stage
berlin-stage:
	$(VIRTUAL_ENV)/bin/locust \
    --locustfile scripts/meinberlin.py \
    --host https://meinberlin-stage.liqd.net

.PHONY: berlin-dev
berlin-dev:
	$(VIRTUAL_ENV)/bin/locust \
    --locustfile scripts/meinberlin.py \
    --host https://meinberlin-dev.liqd.net

.PHONY: berlin-local
berlin-local:
	$(VIRTUAL_ENV)/bin/locust \
    --locustfile scripts/meinberlin.py \
    --host http://127.0.0.1:8003
