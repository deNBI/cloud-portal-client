# Cloud-Portal-Client
The *Cloud Portal Client* is a client written in Python which provides functions to create virtual machines in an OpenStack project.


## Features

 - Create and Delete Instances in an OpenStack project
 - Stop, Resume and Reboot Instances in an OpenStack project
 - Get Flavors and Images from an OpenStack project
 - Creating Snapshots
 - Create and attach volumes to an virtual machine
 - Add floating ips to virtual machines

## Preparation


#### Download and source rc file

Download and source OpenStack RC FILE v3 with the following command:

~~~BASH
source NameOfRcFile.sh
~~~

#### Configuration
You can view (almost) all existing parameters in the [yaml file](VirtualMachineService/config/config.yml).
For local development:
Please copy this file and rename it to `config_local.yml` and fill in missing parameters.
For staging/production setup:
Please copy this file and rename it to `config_YOUR_LOCATION.yml` and fill in missing parameters.
Also you need to provide the path to your config file as the first param when starting a server.

Furthermore there are some parameters you must set in the .env file. Copy the [.env.in](.env.in) to .env and
fill in the missing parameters.
When starting with commandline you will need to export some of them manually.

#### Security Groups
The config file contains a name for the default SimpleVM security group.
It can be configured via the `default_simple_vm_security_group_name` key.
The client will set this group for every SimpleVM machine.

##### Gateway

The client can use a Gateway for starting and stopping machines which allows to use just one floating IP instead of one floating IP per Machine.
You can read [here](ProjectGateway.md) how to setup a gateway on an OpenStack instance.
You can also find complete scripts in the [gateway](gateway) folder.
The client will provide all images with at least one tag, which will be filtered for in the cloud-api.
Also the client provides all flavors, which will also be filtered in the cloud-api.

_**Attention**_: If you are also using the machine where you run the client as a gateway, it is very important to configure the iptables before installing and using docker, otherwise docker could destroy the rules!

##### Persistent IP-Tables
If you are using a gateway, it makes sense to make your iptable rules persistent on this gateway.
To do this, simply install and use this package:

 ~~~BASH
sudo apt-get install iptables-persistent
~~~


#### Create certificates

To create your own certificates follow the instructions on this Website: [thrift certificates](https://thrift.apache.org/test/keys)

_**Attention**_: You need to create your own `Server.pem` and your client needs the appropriate `Client.pem` and `CA.pem`,

## Production


* [Using Docker](#using-docker)


### Using Docker
Specify in the .env file which release should be used by the client.
Then you can start the client with:
```
$ docker-compose up
```
or
```
$ make production
```
_**Attention**_: If you change the port in the [yaml file](VirtualMachineService/config/config.yml) you also need to change the port mapping in the [docker-compose.yml](docker-compose.yml)!

## Development

### Linting

```
$ make lint
```

will run flake8 on the source code directories.


### Documentation

You need thrift to be installed on your machine (see Thrift section).

```
$ make docs
```

will create documentaion in the /docs directory.

### Docker-Compose

Run the following command in order to start the container setup:
Make sure, that your OpenStack RC File is sourced.

```
docker-compose -f docker-compose.dev.yml up --build
```
 or
 ```
make dev
```
You can additionally start bibigrid:
 ```
make dev-bibigrid
```
and additionally also in detached mode:
 ```
make dev-bibigrid-d
```
to list all make commands use:
 ```
make help
```

### Thrift Development

A detailed instruction for installing thrift can be found [here](http://thrift-tutorial.readthedocs.io/en/latest/installation.html).
With the portal_client.thrift you can autogenerate your code.

~~~
make thrift_py
~~~

This command will generate python code from the thrift file.

In order for the cloud-api to use the new/changed methods, [VirtualMachineService.py](VirtualMachineService/VirtualMachineService.py), [ttypes.py](VirtualMachineService/ttypes.py) and [constants.py](VirtualMachineService/constants.py) must be copied over.

Because docker can't use relative imports, you also need to change the import  of [ttypes.py](VirtualMachineService/ttypes.py) in [constants.py](VirtualMachineService/constants.py) and [VirtualMachineService.py](VirtualMachineService/VirtualMachineService.py):

```python
from .ttypes import *

```
```python
from ttypes import *

```
_**Attention**_: The cloud-api needs the files with the relative imports (from .ttypes)!


A detailed instruction, how to write a thrift file can be found on this link: [thrift](http://thrift-tutorial.readthedocs.io/en/latest/usage-example.html#generating-code-with-thrift)

To use the methods declared in the thrift file you need to write a handler which implements the Iface from the VirtualMachineService.
The handler contains the logic for the methods. Then you can start a server which uses your handler.
Example python code for the server:
```python

if __name__ == '__main__':
    with open("s../config.yml", 'r') as ymlfile:
        cfg = yaml.load(ymlfile)
        HOST = cfg['openstack']['host']
        PORT = cfg['openstack']['port']
        CERTFILE = cfg['openstack']['certfile']
    handler=VirtualMachineHandler()
    processor=Processor(handler)
    transport = TSSLSocket.TSSLServerSocket(host=HOST, port=PORT,certfile=CERTFILE)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
    server.serve()
```

### Deployment via ansible

#### 1.Create your inventory file:

Example:

~~~BASH
[test]
REMOTE_IP ansible_user=ubuntu ansible_ssh_private_key_file=PATH_TO_SSH_FILE ansible_python_interpreter=/usr/bin/python3
~~~

where

  * REMOTE_IP is the IP of your staging machine

  * PATH_TO_SSH_FILE is the path to the ssh key of the virtual machine

#### 2.Set SSH keyforwarding

In order to checkout the GitHub project you will have to enable
SSH Key forwarding in your `~/.ssh/config` file.

~~~BASH
Host IP
 ForwardAgent yes
~~~

where `IP` is the IP of the machine you want to start the portal.

#### 3.Set SSH Key in Github

The GitHub repository will cloned using an ssh key you set for the GitHub repository.
You can read how to set an ssh key for the cloud-portal repository on [this website](https://help.github.com/articles/adding-a-new-ssh-key-to-your-github-account/).


#### 4.Install needed libraries

~~~BASH
ansible-galaxy install -r ansible_requirements.yml
~~~

#### 6.Set all variables

Set all variables that can be found in `.env`  and `VirtualMachineService/config/config.yml` file.
You can have more than one `.env` file (`.env` and `.env_*` are not tracked by git) and specify which you want to copy
by using the `env_file` variable.
You can have more than one `VirtualMachineService/config/config.yml` file (`VirtualMachineService/config/config_*` are
not tracked by git) and specify which you want to copy by using the `client_config` variable.
These options are useful when maintaining multiple client sites.

#### 7.Run the playbook

You can run the playbook using the following command:

~~~BASH
ansible-playbook -i inventory_openstack site.yml
~~~

where

  * inventory_openstack is your inventory file which you created in the first step.

  * If you also want to start bibigrid use the tag "bibigrid"
**Choose  different files**

You can also specify different .env, config.yml and server.pem files.

You can also specify branch, tag, commit that should be checked out with `--extra-vars`.

For Example:

~~~BASH
ansible-playbook -i inventory_openstack --extra-vars "repo_version=master" site.yml
~~~
Optional Keys are:
+ repo_version
+ env_file
+ client_server_pem
+ client_config

**Note:** Default repository is always master. Also by default, the files are taken from the folders as for local start.
