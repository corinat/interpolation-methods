
.PHONY: build exec-python exec-gs exec-env down help
# help:                             ## Display a help message detailing commands and their purpose
# 	@echo "Commands:"
# 	@grep -E '^([a-zA-Z_-]+:.*?## .*|#+ (.*))$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
# 	@echo ""

## [Managing container]

build:							## builds the docker container
	docker compose up -d --build
run:							## run the docker container
	docker compose exec python bash
stop:							## stop the docker container
	docker compose down
build-python: 					## run only the python container in the docker compose file
	docker compose up -d --no-deps python
down-python: 					## remove only the python container
	docker compose down python

