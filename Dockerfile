FROM python:3.6.6-slim
ADD . /code
WORKDIR /code
RUN pip install -r requirements.txt
COPY ansible.cfg /etc/ansible/
RUN ansible-galaxy install -r requirements.yml
WORKDIR /code/VirtualMachineService
