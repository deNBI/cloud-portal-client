FROM python:3
ADD . /code
WORKDIR /code
RUN pip install -r requirements.txt
EXPOSE 9090
CMD [ "python3", "-u", "./gen-py/VirtualMachineService/VirtualMachineServer.py" ]