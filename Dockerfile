FROM python:3
ADD . /code
WORKDIR /code
RUN pip install -r requirements.txt
CMD [ "python3", "-u", "./gen-py/VitualMachineService/VirtualMachineServer.py" ]
