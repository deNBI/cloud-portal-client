#!/bin/bash

# Get target hostname or IP address from command line argument
hostname=$1

# Check if hostname is provided
if [ -z "$hostname" ]; then
    echo "Error: No hostname provided."
    echo "Usage: $0 <hostname>"
    exit 1
fi

# Check if input is IP address or hostname
if [[ "$hostname" =~ ^(([1-9]?[0-9]|1[0-9][0-9]|2([0-4][0-9]|5[0-5]))\.){3}([1-9]?[0-9]|1[0-9][0-9]|2([0-4][0-9]|5[0-5]))$ ]]; then
    # Input is IP address
    subj="/C=DE/ST=./L=./O=./CN=$hostname"
    ext="-addext subjectAltName=IP:$hostname"
else
    # Input is hostname
    subj="/C=DE/ST=./L=./O=./CN=$hostname"
    ext=""
fi

# Create a new directory with the provided hostname
mkdir $hostname
cd $hostname

# Generate self-signed certificate and private key
openssl req -new -newkey rsa:2048 -x509 -sha256 -days 365 -nodes -out cert.pem -keyout key.pem -subj "$subj" $ext

# Create CA.pem file by concatenating the cert.pem and key.pem
cat cert.pem key.pem > CA.pem
