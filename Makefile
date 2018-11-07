help:
	@egrep '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'

lint: ## Lint VirtualMachineHandler python code with flake8
	flake8 --ignore=E501,W503 gen-py/VirtualMachineService/VirtualMachineHandler.py


docs: ## Build documentation
	echo test


.PHONY: help lint  docs