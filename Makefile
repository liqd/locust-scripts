VIRTUAL_ENV ?= .

install:
	if [ ! -f $(VIRTUAL_ENV)/bin/python3 ]; then python3 -m venv .; fi
	$(VIRTUAL_ENV)/bin/python3 -m pip install --upgrade -r requirements.txt

run_ae-stage:
	$(VIRTUAL_ENV)/bin/locust \
    --locustfile scripts/ae.py \
    --host https://ae-stage.liqd.net

run_ae-dev:
	$(VIRTUAL_ENV)/bin/locust \
    --locustfile scripts/ae.py \
    --host https://ae-dev.liqd.net

run_ae-localhost:
	$(VIRTUAL_ENV)/bin/locust \
    --locustfile scripts/ae.py \
    --host http://127.0.0.1:8000

run_berlin-stage:
	$(VIRTUAL_ENV)/bin/locust \
    --locustfile scripts/meinberlin.py \
    --host https://meinberlin-stage.liqd.net

run_berlin-dev:
	$(VIRTUAL_ENV)/bin/locust \
    --locustfile scripts/meinberlin.py \
    --host https://meinberlin-dev.liqd.net

run_berlin-localhost:
	$(VIRTUAL_ENV)/bin/locust \
    --locustfile scripts/meinberlin.py \
    --host http://127.0.0.1:8000
