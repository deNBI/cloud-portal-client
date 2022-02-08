FROM python:3.10.1-buster
RUN  apt-get update -y
RUN apt-get install -y build-essential
WORKDIR /code
ADD requirements.txt /code
RUN pip install -r requirements.txt
ADD requirements.yml /code
ADD ansible.cfg /etc/ansible/
RUN ansible-galaxy install -r requirements.yml
ADD . /code
WORKDIR /code/simple_vm_client
