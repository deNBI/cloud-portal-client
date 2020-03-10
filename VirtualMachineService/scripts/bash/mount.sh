#!/bin/bash
sudo mkdir -p david
sudo touch test
declare -a  VOLUME_IDS
for id in "${VOLUME_IDS[@]}"
do
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
  cd /dev/disk/by-id || exit
 sudo mkfs.ext4 "$id"
 sudo mkdir -p /mnt/volume
 sudo chmod 777 /mnt/volume/
 sudo  mount "$id" /mnt/volume
done
