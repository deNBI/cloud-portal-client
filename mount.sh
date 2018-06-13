#!/bin/bash

VOLUME=VOLUMEID

while :
do
  if [ -e /dev/disk/by-id/$VOLUME ];
  then
    echo "volume found";
    break;
  else
    echo "no volume found";
    sleep 10
  fi;
done
cd /dev/disk/by-id
mkfs.ext4 $VOLUME
mkdir -p /mnt/volume
chmod 777 /mnt/volume/
mount $VOLUME /mnt/volume
