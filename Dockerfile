FROM python:3
ADD . /code
WORKDIR /code/gen-py/VirtualMachineService
RUN pip install -r ../../requirements.txt
ENV OS_PROJECT_ID  0
ENV OS_PROJECT_NAME  0
ENV OS_USER_DOMAIN_NAME  0
ENV OS_USERNAME  0
ENV OS_PASSWORD  0
ENV OS_AUHT_URL  0

#docker build -t cloud-portal-client .
#docker run -p 9090:9090 -e OS_AUTH_URL=$OS_AUTH_URL -e OS_PROJECT_ID=$OS_PROJECT_ID -e OS_PROJECT_NAME=$OS_PROJECT_NAME -e OS_USERNAME=$OS_USERNAME -e OS_PASSWORD=$OS_PASSWORD -e OS_USER_DOMAIN_NAME=$OS_USER_DOMAIN_NAME -it cloud-portal-client python3 VirtualMachineServer.py
