FROM python:3
ADD . /code
WORKDIR /code/gen-py/VirtualMachineService
RUN pip install -r ../../requirements.txt
CMD CMD [ "python", "./VirtualMachineServer.py" ]
