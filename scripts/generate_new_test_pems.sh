#!/usr/bin/expect
echo Creating new dir "new_pem"
mkdir $1
cd $1
if [[ "$1" =~ ^(([1-9]?[0-9]|1[0-9][0-9]|2([0-4][0-9]|5[0-5]))\.){3}([1-9]?[0-9]|1[0-9][0-9]|2([0-4][0-9]|5[0-5]))$ ]]; then
  openssl req -new -x509 -nodes -days 3000 -out server.crt -keyout server.key -subj "/C=DE/ST=./L=./O=./CN=$1" --addext "subjectAltName=IP:$1"
else
  openssl req -new -x509 -nodes -days 3000 -out server.crt -keyout server.key -subj "/C=DE/ST=./L=./O=./CN=$1"

fi
openssl x509 -in server.crt -text > CA.pem
cat server.crt server.key > server.pem
openssl pkcs12 -export -clcerts -in server.crt -inkey server.key -out server.p12  -passout pass:thrift
openssl genrsa -out client.key
openssl req -new -nodes -key client.key -out client.csr  -subj "/C=DE/ST=./L=./O=./CN=$1" -passin pass:thrift
openssl x509 -req -days 3000 -in client.csr -CA CA.pem -CAkey server.key -set_serial 01 -out client.crt
openssl pkcs12 -export -clcerts -in client.crt -inkey client.key -out client.p12  -passout pass:thrift
openssl pkcs12 -in client.p12 -out client.pem -clcerts  -passin pass:thrift -passout pass:thrift
openssl rsa -in client.pem -out client_no_pass.pem   -passin pass:thrift
sed -i '/-----BEGIN ENCRYPTED PRIVATE KEY-----/Q' client.pem
cat client_no_pass.pem >> client.pem
find . -type f -not -name '*.pem' -print0  | xargs -0 rm
rm client_no_pass.pem
