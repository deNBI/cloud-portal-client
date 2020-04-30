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
	cp -a gen-py/VirtualMachineService/. VirtualMachineService
	rm -rf gen-py
	@echo Remember to fix the imports: for pip relative imports are needed, for others absolute imports
	
dev-build: ## Build and Start the docker-compose.dev.yml
	docker-compose -f docker-compose.dev.yml up --build
	
dev: ## Build and Start the docker-compose.dev.yml
	docker-compose -f docker-compose.dev.yml up 
	
production: ## Build Release from .env
	docker-compose -f docker-compose.yml up --build -d
	
changelog: ## Generate Changelog
	github_changelog_generator --token  $(t) --release-branch $(b)



.PHONY: help lint  docs thrift_py
