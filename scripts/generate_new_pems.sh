#!/usr/bin/expect

# Check if the correct number of arguments was passed
if [ $# -ne 4 ]; then
    echo "Usage: $0 <server_common_name> <server_ip> <client_common_name> <client_ip>"
    exit 1
fi

# Set the arguments to variables
server_cn=$1
server_ip=$2
client_cn=$3
client_ip=$4

# Replace dots with underscores in server_cn and client_cn
server_cn_dir=${server_cn//./_}
client_cn_dir=${client_cn//./_}
dir_name="pem_files_${server_cn_dir}_${client_cn_dir}"
echo "Creating new directory: $dir_name"

mkdir "$dir_name"

# Move into the new directory
cd "$dir_name"

# Generate CA certificate and key
openssl req -new -x509 -nodes -days 365 -keyout ca.key -out ca.crt -subj "/C=DE/ST=./L=./O=./CN=deNBI"
cat ca.crt ca.key > CA_$server_cn_dir.pem
if [[ "$server_ip" =~ ^(([1-9]?[0-9]|1[0-9][0-9]|2([0-4][0-9]|5[0-5]))\.){3}([1-9]?[0-9]|1[0-9][0-9]|2([0-4][0-9]|5[0-5]))$ ]]; then
  openssl req -new   -nodes -out server.csr -keyout server.key -subj "/C=DE/ST=./L=./O=./CN=$server_cn" --addext "subjectAltName=IP:$server_ip"
else
  openssl req -new  -nodes -out server.csr -keyout server.key -subj "/C=DE/ST=./L=./O=./CN=$server_cn"

fi
echo "[req]" > ext.conf
echo "distinguished_name = req_distinguished_name" >> ext.conf
echo "req_extensions = v3_req" >> ext.conf
echo "" >> ext.conf
echo "[req_distinguished_name]" >> ext.conf
echo "CN = $server_cn" >> ext.conf
echo "" >> ext.conf
echo "[v3_req]" >> ext.conf
echo "subjectAltName = IP:$server_ip" >> ext.conf

# Create server certificate and key
openssl x509  -req   -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 365 -extfile  ext.conf --extensions v3_req

rm ext.conf
# Create CA certificate and PEM file for server
cat  server.crt server.key  > server_$server_cn_dir.pem

# Create client certificate and key
if [[ "$client_ip" =~ ^(([1-9]?[0-9]|1[0-9][0-9]|2([0-4][0-9]|5[0-5]))\.){3}([1-9]?[0-9]|1[0-9][0-9]|2([0-4][0-9]|5[0-5]))$ ]]; then
  openssl req -new  -nodes -out client.csr -keyout client.key  -subj "/C=DE/ST=./L=./O=./CN=$client_cn" --addext "subjectAltName=IP:$client_ip"
else
  openssl req -new  -nodes -out client.csr -keyout client.key  -subj "/C=DE/ST=./L=./O=./CN=$client_cn"

fi

# Create temporary ext.conf file for client
echo "[req]" > ext.conf
echo "distinguished_name = req_distinguished_name" >> ext.conf
echo "req_extensions = v3_req" >> ext.conf
echo "" >> ext.conf
echo "[req_distinguished_name]" >> ext.conf
echo "CN = $client_cn" >> ext.conf
echo "" >> ext.conf
echo "[v3_req]" >> ext.conf
echo "subjectAltName = IP:$client_ip" >> ext.conf

openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 365 -extfile  ext.conf  --extensions v3_req

rm ext.conf
cat  client.crt client.key   > client_$client_cn_dir.pem

# Remove unnecessary files
find . -type f -not -name '*.pem' -print0  | xargs -0 rm

echo "Done!"
