# cloud-portal-client

## Deployment
There are 2 ways to run the cloud-portal-client.

# 1.run with docker: 
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

_**Attention**_: You need to create your own `Server.pem`,
for testing / play around purposes **only**.

### create certificates

To create your own certificates follow the instructions on this Website: [thrift certificates](https://thrift.apache.org/test/keys)

### download rc file 

Download your openstack rc file which contains your openstack configuration.
you can find the rc file, by logging into [openstack](https://openstack.cebitec.uni-bielefeld.de)
then going to the [access & security](https://openstack.cebitec.uni-bielefeld.de/horizon/project/access_and_security/) tab.
Choose API Access and press the button: Download Openstack RC FILE v3.
Finally move this file into the cloud-portal-client folder.

### Configuration

Before starting the client you need to set your configuration in the config.yml file.

* server_port= port to host
* server_host= host ip
* server_cert= path to server.pem

### Starting the cloud-portal-client

To start application your terminal need to be in the 'cloud-portal-client' folder then execute the following commands
~~~BASH
$> sudo docker build -t cloud-portal-client .
$> sudo docker run -p 9090:9090 -it cloud-portal-client
~~~

the terminal will ask you now to enter your openstack password to finish configuration.


# 2. run without docker:
 you will need to have python 3.6 and pip installed.

#### install python3
 Linux:
 sudo apt-get install python3.6

#### install pip
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


### create certificates

To create your own certificates follow the instructions on this Website: [thrift certificates](https://thrift.apache.org/test/keys)

### installing required libraries

to install all required python libraries run the following command:
 ~~~BASH
$> pip install -r requirements.txt
~~~


### download rc file 

Download your openstack rc file which contains your openstack configuration.
you can find the rc file, by logging into [openstack](https://openstack.cebitec.uni-bielefeld.de)
then going to the [access & security](https://openstack.cebitec.uni-bielefeld.de/horizon/project/access_and_security/) tab.
Choose API Access and press the button: Download Openstack RC FILE v3.
Finally move this file into the cloud-portal-client folder.

### source rc file

To load your openstack configuration you need to run the following command in the terminal:

 ~~~BASH
$> source NameOfRcFile.sh
~~~

this will configure your openstack account

### Configuration

Before starting the client you need to set your configuration in the config.yml file.

* server_port = port to host
* server_host= host ip
* server_cert= path to server.pem


### start cloud-portal-client
to finally run the code you need to change the directory and run the correct python file.


 ~~~BASH
$> cd ./gen-py/VirtualMachineService
$> python3 VirtualMachineServer.py 
~~~

_**Attention**_: you need to use the same Terminal you used to source the rc file.
