SHELL := /bin/bash

include .env

image:
	docker build \
		-f Dockerfile \
		-t turnio_suggested_replies:latest \
		-t turnio_suggested_replies:$$(date +%s) \
		.

list:
	docker image ls -a | grep turnio_suggested_replies

remove_container:
	docker container rm suggested_replies_dev

remove_image:
	docker rmi $(docker image ls -a | grep turnio_suggested_replies | awk '{print $3}')

list_containers:
	docker container ls -a | grep suggested_replies_dev

run:
	docker run \
		--rm \
		--env-file .env \
		-e PORT=$(PORT) \
		--name=suggested_replies_dev \
		-p $(PORT):$(PORT) \
		turnio_suggested_replies:latest

redo:
	$(MAKE) mkim
	$(MAKE) run

tunnel:
	ngrok http $(PORT) --subdomain=$(NGROK_SUBDOMAIN) --region=$(NGROK_REGION)

debug:
	FLASK_DEBUG=1 FLASK_APP=main.py flask run --port $(PORT)
