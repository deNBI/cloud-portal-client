FROM python:3.7.7-slim
ADD . /code
WORKDIR /code
RUN  apt-get update -y 
RUN apt install -y build-essential
RUN apt-get install -y python3-dev
RUN pip install -r requirements.txt
COPY ansible.cfg /etc/ansible/
RUN ansible-galaxy install -r requirements.yml
WORKDIR /code/VirtualMachineService
