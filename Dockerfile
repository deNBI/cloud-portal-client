FROM python:3.6.6-slim
ADD . /code
WORKDIR /code
RUN pip install -r requirements.txt
WORKDIR /code/VirtualMachineService
