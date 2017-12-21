# cloud-portal-client
#Development
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
    with open("../../config.yml", 'r') as ymlfile:
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
# 2. Run without docker:
 you will need to have python 3.6 and pip installed.

#### Install python3
 Linux:
 sudo apt-get install python3.6

#### Install pip
 Linux:
 sudo apt-get install -y python3-pip

### Obtaining the software components
Once Python and pip is installed, clone the repository with your SSH key:

~~~BASH
$> git clone https://github.com/deNBI/cloud-portal-client.git
~~~

Enter the new directory called `cloud-portal-client`

~~~BASH
$> cd ./cloud-portal
~~~

Since the current version is developed in the dev branch you need to checkout it manually:

~~~BASH
$>git checkout dev
~~~

_**Attention**_: You need to create your own `Server.pem`,
for testing / play around purposes **only**.


### Create certificates

To create your own certificates follow the instructions on this Website: [thrift certificates](https://thrift.apache.org/test/keys)

### Installing required libraries

to install all required python libraries run the following command:
 ~~~BASH
$> pip install -r requirements.txt
~~~



### Download rc file 

Download your openstack rc file which contains your openstack configuration.
you can find the rc file, by logging into Openstack and 
then going to the access & security tab.
Choose API Access and press the button: Download Openstack RC FILE v3.
Finally move this file into the cloud-portal-client folder.

### Source rc file

To load your openstack configuration you need to run the following command in the terminal:

 ~~~BASH
$> source NameOfRcFile.sh
~~~


### Configuration

Before starting the client you need to set your configuration in the config.yml file.

* port= Port to host
* host= Host ip
* certfile= Path to server.pem
* network = Network where the project is located
* flavor_filter= List of allowed flavor names

### Start cloud-portal-client
To finally run the code you need to change the directory and run the correct python file.


 ~~~BASH
$> cd ./gen-py/VirtualMachineService
$> python3 VirtualMachineServer.py 
~~~

_**Attention**_: you need to use the same Terminal you used to source the rc file.

## Deployment

# 1.Run with docker: 
   You will need a `docker` service up and running to start the client with docker.
   
#### Installing Docker

You can find a detailed instruction how to install docker on this website: [docker](https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/#install-docker-ce)

#### Obtaining the software components

Once docker is installed and running, clone the repository with your SSH key:

~~~BASH
$> git clone https://github.com/deNBI/cloud-portal-client.git
~~~

Enter the new directory called `cloud-portal-client`

~~~BASH
$> cd ./cloud-portal
~~~

Since the current version is developed in the dev branch you need to checkout it manually:

~~~BASH
$>git checkout dev
~~~

_**Attention**_: You need to create your own `Server.pem` and your client need the appropriate `Client.pem` and `CA.pem`,

### Create certificates

To create your own certificates follow the instructions on this Website: [thrift certificates](https://thrift.apache.org/test/keys)

### Download rc file 

Download your openstack rc file which contains your openstack configuration.
you can find the rc file, by logging into Openstack and 
then going to the access & security tab.
Choose API Access and press the button: Download Openstack RC FILE v3.
Finally move this file into the cloud-portal-client folder.

### Configuration

Before starting the client you need to set your configuration in the config.yml file.

* port= Port to host
* host= Host ip
* certfile= Path to server.pem
* network = Network where the project is located
* flavor_filter= List of allowed flavor names

### Starting the cloud-portal-client

To start application your terminal need to be in the 'cloud-portal-client' folder then execute the following commands
~~~BASH
$> sudo docker build -t cloud-portal-client .
$> sudo docker run -p 9090:9090 -it cloud-portal-client
~~~
_**Attention**_: You need to set the port mapping ( for example `9090:9090`) to the port used in your config.yml!.
The terminal will ask you now to enter your openstack password to finish your  configuration.



