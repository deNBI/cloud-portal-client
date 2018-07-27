FROM ubuntu:16.04 as builder
RUN apt update && apt install -y curl
WORKDIR /
RUN curl -L -O https://artifacts.elastic.co/downloads/beats/filebeat/filebeat-6.3.0-amd64.deb

FROM python:3.6.6-slim
ADD . /code
WORKDIR /code
RUN pip install -r requirements.txt
WORKDIR /code/gen-py/VirtualMachineService
COPY --from=builder /filebeat-6.3.0-amd64.deb  .
RUN dpkg -i filebeat-6.3.0-amd64.deb && rm -rf filebeat-6.3.0-amd64.deb
