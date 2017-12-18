# cloud-portal-client

## Deployment
There are 2 ways to run the cloud-portal-client.
# 1.run with docker: 
   You will need a `docker` service up and running and `docker-compose` to start the solution:
#### Installing Docker
You can find a detailed instruction how to install docker on https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/#install-docker-ce
#### Obtaining the software components

Once docker is installed and running and docker-compose is installed as well, clone the repository with your SSH key:

~~~BASH
$> git clone https://github.com/deNBI/cloud-portal-client.git
~~~

Enter the new directory called `cloud-portal-client`

~~~BASH
$> cd ./cloud-portal
~~~

Since the current version is developed in the dev_thrift branch you need to checkout it manually:

~~~BASH
$>git checkout dev_thrift
~~~

_**Attention**_: You need to create your own `Server.pem`, `Client.pem`, `CA.pem`
for testing / play around purposes **only**.

### create certificates

To create your own certificates follow the instructions on this Website: https://thrift.apache.org/test/keys


### Starting the cloud-portal-client

To start application your terminal need to be in the 'cloud-portal-client' folder then excecute the following commands
~~~BASH
$> sudo docker-compose build
$> sudo docker-compose up
~~~

### Configuration

Before starting the client you need to set your configuration in the config.py file.

* username = your openstack username
* password = your openstack password
* network = network to connect
* auth_url= your project --> access & security --> view Credentials --> Authentication URL
* project_name = name of the project to connect
* user_domain_name = default or your settings
* project_domain_name = default or your settings
* server_port = port to host
* server_host= host ip
* server_cert= path to server.pem

when starting the client with docker you also need to change the ports in the Dockerfile and in the docker-compose.yml file to the port you are using.


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

Since the current version is developed in the dev_thrift branch you need to checkout it manually:

~~~BASH
$>git checkout dev_thrift
~~~

_**Attention**_: You need to create your own `Server.pem`, `Client.pem`, `CA.pem`
for testing / play around purposes **only**.

### create certificates

To create your own certificates follow the instructions on this Website: https://thrift.apache.org/test/keys

### installing required libraries

to install all required python libraries run the following command:
 ~~~BASH
$> pip install -r requirements.txt
~~~

### start cloud-portal-client
to finally run the code you need to change the directory and run the right python file.

 ~~~BASH
$> cd ./gen-py/VirtualMachineService
$> python3 VirtualMachineServer.py 
~~~

### Configuration

Before starting the client you need to set your configuration in the config.py file.

* username = your openstack username
* password = your openstack password
* network = network to connect
* auth_url= your project --> access & security --> view Credentials --> Authentication URL
* project_name = name of the project to connect
* user_domain_name = default or your settings
* project_domain_name = default or your settings
* server_port = port to host
* server_host= host ip
* server_cert= path to server.pem
