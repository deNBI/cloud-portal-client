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
Also you need to provide the path to your config file as the first param when starting a server.

Furthermore there are some parameters you can set in the [.env.in](.env.in) file, which are read only when starting with docker.  
Important: You need to rename .env.in to .env in order for it to be read by docker.  
When starting with commandline you will need to export some of them manually.

#### Security Groups
The client expects a security group with the name "defaultSimpleVM" to exist which will be assigned to each machine at startup. Also, each machine will have its own security group when it starts.

##### Gateway

The client can use a Gateway for starting and stopping machines which allows to use just one floating IP instead of one floating IP per Machine.
You can read [here](ProjectGateway.md) how to setup a gateway on an OpenStack instance.
You can also find complete scripts in the [gateway](gateway) folder.
The client will provide all images with at least one tag, which will be filtered for in the cloud-api. 
Also the client provides all flavors, which will also be filtered in the cloud-api.

_**Attention**_: If you are also using the machine where you run the client as a gateway, it is very important to configure the iptables before installing and using docker, otherwise docker could destroy the rules!


#### Create certificates

To create your own certificates follow the instructions on this Website: [thrift certificates](https://thrift.apache.org/test/keys)

_**Attention**_: You need to create your own `Server.pem` and your client needs the appropriate `Client.pem` and `CA.pem`,

## Production

There are separate ways to use the portal-cloud-client:

* [Using pip](#using-pip)
* [Using Docker](#using-docker)

### Using pip

You need to have python3.6 and pip installed.

Than install the cloud-portal-client with pip:

 ~~~BASH
pip install git+https://github.com/deNBI/cloud-portal-client.git
~~~

#### Commandline client

If you set your configuration you can start the portal-client:

 ~~~BASH
portal_client_start_server path/to/config.yml
~~~


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
        HOST = cfg['openstack_connection']['host']
        PORT = cfg['openstack_connection']['port']
        CERTFILE = cfg['openstack_connection']['certfile']
    handler=VirtualMachineHandler()
    processor=Processor(handler)
    transport = TSSLSocket.TSSLServerSocket(host=HOST, port=PORT,certfile=CERTFILE)
    tfactory = TTransport.TBufferedTransportFactory()
    pfactory = TBinaryProtocol.TBinaryProtocolFactory()
    server = TServer.TSimpleServer(processor, transport, tfactory, pfactory)
    server.serve()
```
