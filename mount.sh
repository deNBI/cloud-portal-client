#!/bin/bash

while :
do
  if [ -e /dev/disk/by-id* ];
  then
    echo "found volume";
    break;
  else
    echo "no volume found";
    sleep 10
  fi;
done
cd /dev/disk/by-id
FILE=$(ls | sort -n | head -1)
mkfs.ext4 $FILE
mkdir -p /mnt/volume
chmod 777 /mnt/volume/
mount $FILE /mnt/volume