#!/bin/bash
sudo mkdir -p david
touch test
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
  mkfs.ext4 "$id"
  mkdir -p /mnt/volume
  chmod 777 /mnt/volume/
  mount "$id" /mnt/volume
done
