FROM python:3
ADD . /code
WORKDIR /code/gen-py/VirtualMachineService
RUN pip install -r ../../requirements.txt
RUN curl -L -O https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-6.3.0-amd64.deb
RUN dpkg -i filebeat-6.3.0-amd64.deb
