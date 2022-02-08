help:
	    @egrep '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

lint: ## Lint VirtualMachineHandler python code with flake8

	    flake8 --ignore=W503,D104 VirtualMachineService/VirtualMachineHandler.py VirtualMachineService/scripts


docs: ## Build documentation
	rm -rf docs
	mkdir docs
	@echo Building documentation
	thrift --gen html portal_client.thrift
	cp -a gen-html/. docs
	rm -rf gen-html

thrift_py: ## Builds python code from thrift file
	thrift --gen py portal_client.thrift
	cp -a gen-py/VirtualMachineService/. simple_vm_client
	rm -rf gen-py
	@echo Remember to fix the imports: for pip relative imports are needed, for others absolute imports

dev-build: ## Build and Start the docker-compose.dev.yml
	docker-compose -f docker-compose.dev.yml up --build

dev-d: ## Build and Start the docker-compose.dev.yml
	docker-compose -f docker-compose.dev.yml up -d

dev-build-d: ## Build and Start the docker-compose.dev.yml
	docker-compose -f docker-compose.dev.yml up --build -d

dev: ## Build and Start the docker-compose.dev.yml
	docker-compose -f docker-compose.dev.yml up

dev-build-bibigrid: ## Build and Start the docker-compose.dev.yml with bibigrid
	docker-compose -f docker-compose.dev.bibigrid.yml up --build

dev-bibigrid: ## Build and Start the docker-compose.dev.yml with bibigrid
	docker-compose -f docker-compose.dev.bibigrid.yml up

dev-build-bibigrid-d: ## Build and Start the docker-compose.dev.yml with bibigrid
	docker-compose -f docker-compose.dev.bibigrid.yml up --build -d

dev-bibigrid-d: ## Build and Start the docker-compose.dev.yml with bibigrid
	docker-compose -f docker-compose.dev.bibigrid.yml up -d

production: ## Build Release from .env
	docker-compose -f docker-compose.yml up --build -d

production-bibigrid: ## Build Release from .env and with bibigrid
	docker-compose -f docker-compose.bibigrid.yml up --build -d

client_logs: ## Logs from Client
	docker logs client_portal-client_1

bibigrid_logs: ## Logs from Bibigrid
	docker logs client_bibigrid_1

enter_client_container: ## Enter Client container
	docker exec -it client_portal-client_1 bash

check_env: ## Checks if your .env contains every key set in .env.in.
	python3 check_env.py .env.in .env env

check_manual_env: ## Checks if your specified .env_* contains every key set in .env.in.
	python3 check_env.py .env.in $(env-file) env

check_local_config: ## Check if your config_local.yml contains every key set in config.yml
	python3 check_env.py VirtualMachineService/config/config.yml VirtualMachineService/config/config_local.yml config

check_manual_config: ## Check if your specified config_*.yml contains every key set in config.yml
	python3 check_env.py VirtualMachineService/config/config.yml VirtualMachineService/config/$(config-file) config


.PHONY: help lint  docs thrift_py
