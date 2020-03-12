#!/bin/bash
sudo touch test
declare -a volumes=VOLUME_IDS
declare -a paths=VOLUME_PATHS
ITER=0
for id in "${volumes[@]}"
do
  while :
  do
    if [ -e /dev/disk/by-id/"$id" ];
    then
      echo "volume  ""$id"" found";
      break;
    else
      echo "no volume ""$id"" found";
      sleep 10
    fi;
  done
 cd /dev/disk/by-id || exit
 sudo mkfs.ext4 "$id"
 sudo mkdir -p /mnt/${paths[ITER]}
 sudo chmod 777 /mnt/${paths[ITER]}/
 sudo  mount "$id" /mnt/${paths[ITER]}
done
