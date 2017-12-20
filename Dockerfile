FROM python:3
ADD . /code
WORKDIR /code/gen-py/VirtualMachineService
RUN pip install -r ../../requirements.txt
RUN chmod +x ../../openstackrc.sh
RUN rm /bin/sh && ln -s /bin/bash /bin/sh
CMD  source ../../openstackrc.sh && python -u VirtualMachineServer.py

#docker build -t cloud-portal-client .
#docker run -p 9090:9090 -i -t cloud-portal-client
