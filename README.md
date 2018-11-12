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

#### Install python3

Linux:
~~~BASH
$> sudo apt-get install python3.6
~~~



#### Install pip
Linux:
~~~BASH
$> sudo apt-get install -y python3-pip
~~~

#### Download rc file

Download your OpenStack RC file which contains your OpenStack configuration.
You can find the RC file by logging into OpenStack and
then choosing to the access & security tab.
Choose API Access and press the button: Download Openstack RC FILE v3.
Finally, move this file into the cloud-portal-client folder.

#### Source rc file
To load your OpenStack configuration you need to run the following command in the terminal:

 ~~~BASH
$> source NameOfRcFile.sh
~~~

#### Create certificates

To create your own certificates follow the instructions on this Website: [thrift certificates](https://thrift.apache.org/test/keys)

_**Attention**_: You need to create your own `Server.pem` and your client needs the appropriate `Client.pem` and `CA.pem`,

## Usage
There are seperate ways to use the portal-cloud-client:

* [Using pip](#using-pip)
* [Cloning the repository](#cloning-the-repository)
    * [Using Docker](#with-docker)
    * [Without Docker](#without-docker)




### Using pip
First install the cloud-portal-client with pip:

 ~~~BASH
$> pip install git+https://github.com/deNBI/cloud-portal-client.git@feature/docs_makefile
~~~

#### Commandline client

Then a configuration must be created:

 ~~~BASH
$> portal_client_create_config
~~~

You can always reset your configuration with this command.
If you only want to view your configuration use this command:

 ~~~BASH
$> portal_client_show_config
~~~

If you set your configuration you can start the portal-client:

 ~~~BASH
$> portal_client_start_server
~~~



### Cloning the repository

Clone the repository
~~~BASH
$> git clone https://github.com/deNBI/cloud-portal-client.git
~~~

Enter the new directory called `cloud-portal-client`

~~~BASH
$> cd cloud-portal-client
~~~

#### Configuration

Before starting the client you need to set your configuration in the config.yml file located in the VirtualMachineService/config folder.
'''yaml
openstack_connection
    port: port to use
    host: ip of the host
    jumphost_base: port of jumphost
    jumphost_Ip: ip of jumphost
    tag: tag which the client uses to filter images/flavors
    use_jumphost: If "True" Jumphost will be used. If "False" Jumphost won't be used. You can read [here](ProjectGateway.md) how to setup a gateway for OpenStack.
    certfile: Path to server.pem
    network: Network where the project is located
'''


To filter which images and flavors to use the client uses the tag attribute for the image and the extra_specs attribute for flavors.
The client will forward all images which have the tag 'portalclient' and the client will also forward all flavors which have portalclient = True in their extra_specs.


### With Docker
#### Installing Docker

You can find a detailed instruction how to install docker on this website: [docker](https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/#install-docker-ce)



### Starting the cloud-portal-client

To start the application your terminal need to be in the 'cloud-portal-client' folder (where the Dockefile is located) then execute the following commands:
~~~BASH
$> sudo docker build -t cloud-portal-client .
$> sudo docker run -p 9090:9090 -e OS_AUTH_URL=$OS_AUTH_URL -e OS_PROJECT_ID=$OS_PROJECT_ID -e OS_PROJECT_NAME=$OS_PROJECT_NAME -e OS_USERNAME=$OS_USERNAME -e OS_PASSWORD=$OS_PASSWORD -e OS_USER_DOMAIN_NAME=$OS_USER_DOMAIN_NAME -it cloud-portal-client python3 VirtualMachineServer.py
~~~
_**Attention**_: You need to set the port mapping ( for example `9090:9090`) to the port used in your config.yml !


###  Without Docker
You will need to have python 3.6 and pip installed.


### Installing required libraries

To install all required python libraries run the following command:
 ~~~BASH
$> pip install -r requirements.txt
~~~

### Start cloud-portal-client
To finally run the code you need to change the directory and run the correct python file.

 ~~~BASH
$> cd VirtualMachineService
$> python3 VirtualMachineServer.py 
~~~

_**Attention**_: You need to use the same Terminal you used to source the rc file.



# Development
## Thrift Development
You need thrift installed.
A detailed instruction can be found under [thrift-installation](http://thrift-tutorial.readthedocs.io/en/latest/installation.html).
With the portal_client.thrift you can autogenerate your code.

~~~BASH
thrift -r --gen py portal_client.thrift
~~~

This command will generate python code from the thrift file.
A detailed instruction, how to write a thrift file can be found on this link: [thrift](http://thrift-tutorial.readthedocs.io/en/latest/usage-example.html#generating-code-with-thrift)

To use the methods declared in the thrift file you need to write a handler which implements the Iface from the VirtualMachineService. The handler contains the logic for the methods.
Then you can start a server which uses your handler.
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



