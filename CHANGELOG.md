##  (2020-06-18)


#### Features

* **Ansible:** specify port added ([33609ccc](33609ccc))
* **resenv:**  rstudio creates profiles file ([e68b4718](e68b4718))

##  (2020-03-19)


#### Features

* **Volume:** mounted path and attach volumes by start ([82c50883](82c50883))

#### Bug Fixes

* **Linting:** blacked code ([9200bdf7](9200bdf7))
* **request:**  add production boolean to config ([a083298a](a083298a))

##  (2020-03-13)


#### Features

* **Volume:** added resizing
* **mosh:**  playbook for installing mosh

##  (2020-02-27)


#### Bug Fixes

* **filebeat:**  elastic output url as variable ([423dbfc0](423dbfc0))

#### Features

* **filebeat:**  container harvesting client logs ([87d46a57](87d46a57))


##  (2020-02-23)


#### Features

* **Make:** added make dev without build ([efa5d67f](efa5d67f))

#### Bug Fixes

* **forc:**  ssl verification ([f6b717a0](f6b717a0))
##  (2020-02-21)

#### Refactor

* **Research Environments:** forc get-url method refactor

##  (2020-02-18)

#### Features

* **troubleshooting:**  add troubleshooting page for client ([c7ffe62e](c7ffe62e))

##  (2020-01-31)

#### Bug Fixes

* **vm:**  also check and set error state ([f1373adf](f1373adf))

##  (2020-01-24)

#### Features

* **resenv:** resenvs as modes working ([7a12746](7a12746))


##  (2020-01-19)


#### Bug Fixes

* **bioconda:**  creates and deploys playbook again ([76f61694](76f61694))

##  (2020-01-15)


#### Features

* **Modi:** added more Methods ([f1f357b5](f1f357b5))


##  (2020-01-09)


#### Features

* **Cluster:**
  * cluster model ([6e1d45b3](6e1d45b3))
  * terminate and create ([738e2b65](738e2b65))

##  (2020-01-06)


#### Bug Fixes

* **conda:**  change user variable ([bbd486b9](bbd486b9))

#### Features

* **images:**
  *  cross check imagetags with forc (#196) ([b32190c4](b32190c4))
  *  cross check imagetags with forc ([d39c3f5e](d39c3f5e))

##  (2019-12-19)


#### Features

* **resenv:**  theiaide, guacamole working ([0f390ce8](0f390ce8))
##  (2019-12-17)


#### Bug Fixes

* **UDP:** fixed the UDP group ([a51d025c](a51d025c))

##  (2019-12-12)


#### Bug Fixes

* **forc-key:**  load forc_api_key from os.environment ([33ce6328](33ce6328))



##  (2019-12-06)


#### Features

* **client:**  multiple security groups for single vms ([52990be6](52990be6))


##  (2019-11-19)


#### Bug Fixes

* **Bioconda:** also fixed bioconda ([6b9e74db](6b9e74db))
* **Flavor:** also for giessen ([49312ce8](49312ce8))

#### Features

* **Client:** added docker with image tag in env ([adacf7bc](adacf7bc))

##  (2019-11-14)


#### Features

* **Client:**
  * updated readme ([6704108f](6704108f))
  * updated readme ([de9c6fc5](de9c6fc5))
* **Instance:** starts with defualtSimpleVm security group ([ed9d9e31](ed9d9e31))

##  (2019-11-13)


#### Bug Fixes

* **security-group:**  return from function when sec-g already exists ([5ebed609](5ebed609))

##  (2019-11-07)

### Refactors

* **readme:**  update readme

##  (2019-10-25)


#### Bug Fixes

* **conda-install:**  conda installing again ([a3161071](a3161071))
* **playbook:**  user key task always run, fix miniconda3 version, ansible==2.7.14 ([c2d88857](c2d88857))


##  (2019-10-24)


#### Bug Fixes

* **conda-install:**  conda installing again ([a3161071](a3161071))
* **playbook:**  user key task always run, fix miniconda3 version, ansible==2.7.14 ([c2d88857](c2d88857))


##  (2019-10-16)


#### Features

* **Config:** added port calc in config ([86b74c0e](86b74c0e))

##  (2019-10-08)

### Bug Fixes

* **delete-vm:**
  *  deletes all security groups of server with the same name

### Features

* **bioconda:** init .bashrc and create alias for environment (#141)

##  (2019-09-11)


#### Bug Fixes

* **bioconda:**
  *  now able to install only one package (#139) (#140) ([48e91dfd](48e91dfd))

##  (2019-09-03)


#### Features

* **OpenStack:** sync db with openstack ([ec1ef3e5](ec1ef3e5))

##  (2019-08-08)


#### Bug Fixes

* **Virtualmachine:** not timeout when stopping or resuming vm ([3b435835](3b435835))
* **playbook:**  try except for _vars_file.yml ([58c97068](58c97068))
* **vm:**  stops instead of suspending ([085f7f74](085f7f74))

##  (2019-07-10)


#### Features

* **Snapshot:** addeed description ([e7570b12](e7570b12))

#### Bug Fixes

* **ansible:**  fix string.strip error ([dafd8045](dafd8045))


##  (2019-06-18)

#### Refactor

* **Config:** added defaultopenstack param

##  (2019-05-28)


##  (2019-06-11)

#### Refactor

* **Loggin:** filehandler logs to /log/portal_client_log, removed filebeat from dockerfile

##  (2019-05-28)


#### Features

* **Client:**  added info when rc file isn't sourced ([19121659](19121659))
* **SecurityGroups:** added security groups" ([282b2e9d](282b2e9d))

#### Bug Fixes

* **Project:** added project domain id ([9e8bd566](9e8bd566))

#### Features

* **Snapshot:** check status



### Features

* **PR_TEMPLATE:**
  * updated with changelog"
  * added comment checks
* **pep:**  set line max length to 100
