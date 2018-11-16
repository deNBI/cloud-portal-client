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

Download and source Openstack RC FILE v3 with the following command:

~~~BASH
source NameOfRcFile.sh
~~~

#### Create certificates

To create your own certificates follow the instructions on this Website: [thrift certificates](https://thrift.apache.org/test/keys)

_**Attention**_: You need to create your own `Server.pem` and your client needs the appropriate `Client.pem` and `CA.pem`,

## Production

There are seperate ways to use the portal-cloud-client:

* [Using pip](#using-pip)
* [Using Docker](#using-docker)

### Using pip

You need to have python3.6 and pip installed.

Than install the cloud-portal-client with pip:

 ~~~BASH
pip install git+https://github.com/deNBI/cloud-portal-client.git
~~~

#### Commandline client

You need to have a configuration for the client.
Just create your own yaml.file with the params described in [Configuration](#configuration) or use:

 ~~~BASH
portal_client_create_config
~~~

To see your view your default configuration use this command:

 ~~~BASH
portal_client_show_config
~~~

If you set your configuration you can start the portal-client:

 ~~~BASH
portal_client_start_server
~~~

##### Optional params
Options:
* --config TEXT  path to the config file
* --zone TEXT    The name of the availability zone the servers should be a part of.

#### Configuration

You can provide your configuration in the config.yml file placed in the VirtualMachineService/config folder.
~~~yaml
openstack_connection:
    port: port to use
    host: ip of the host
    jumphost_base: port of jumphost
    jumphost_Ip: ip of jumphost
    tag: tag which the client uses to filter images/flavors
    use_jumphost: If "True" Jumphost will be used. If "False" Jumphost won't be used.
    certfile: Path to server.pem
    network: Network where the project is located
~~~

You can read [here](ProjectGateway.md) how to setup a gateway for OpenStack.
The client will provide all images which have the tag 'portalclient' and all flavors which have portalclient = True in their extra_specs.

### Using Docker

You can use the Docker image `denbicloud/cloud-portal-client` with the configuration parameters provided in `docker-compose.yml`

# Development

## Linting

```
$ make lint
```

will run flake8 on the source code directories.


## Documentation

```
$ make docs
```

will create documentaion in the /docs directory.


## Thrift Development

A detailed instruction for installing thrift can be found [here](http://thrift-tutorial.readthedocs.io/en/latest/installation.html).
With the portal_client.thrift you can autogenerate your code.

~~~
make thrift_py
~~~

This command will generate python code from the thrift file.
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
