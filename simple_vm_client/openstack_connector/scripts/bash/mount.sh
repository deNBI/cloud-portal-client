#!/bin/bash
sudo touch test
declare -a volumes_new=VOLUME_IDS_NEW
declare -a paths_new=VOLUME_PATHS_NEW
declare -a volumes_attach=VOLUME_IDS_ATTACH
declare -a paths_attach=VOLUME_PATHS_ATTACH

ITER=0
ABORT_COUNTER=0
for id in "${volumes_new[@]}"; do
  while :; do
    if [ -e /dev/disk/by-id/"$id" ]; then
      echo "volume  ""$id"" found"
      ABORT_COUNTER=0
      break
    else
      echo "no volume ""$id"" found"
      if [ $ABORT_COUNTER -gt 12 ]; then
        break
      fi
      ((ABORT_COUNTER++))

      sleep 10
    fi
  done
  if [ $ABORT_COUNTER -gt 12 ]; then
    echo "Waited 120 seconds for ""$id"" "
    ABORT_COUNTER=0

    continue
  fi
  cd /dev/disk/by-id || exit
  sudo mkfs.ext4 "$id"
  sudo mkdir -p /vol//${paths_new[ITER]}
  sudo chmod 777 /vol//${paths_new[ITER]}/
  sudo mount "$id" /vol//${paths_new[ITER]}
  ((ITER++))
done
ITER=0
ABORT_COUNTER=0
for id in "${volumes_attach[@]}"; do
  while :; do
    if [ -e /dev/disk/by-id/"$id" ]; then
      echo "volume  ""$id"" found"
      ABORT_COUNTER=0
      break
    else
      echo "no volume ""$id"" found"
      if [ $ABORT_COUNTER -gt 12 ]; then
        break
      fi
      ((ABORT_COUNTER++))

      sleep 10
    fi
  done
  if [ $ABORT_COUNTER -gt 12 ]; then
    echo "Waited 120 seconds for ""$id"" "
    ABORT_COUNTER=0

    continue
  fi
  cd /dev/disk/by-id || exit
  sudo mkdir -p /vol//${paths_attach[ITER]}
  sudo chmod 777 /vol//${paths_attach[ITER]}/
  sudo mount "$id" /vol//${paths_attach[ITER]}
  ((ITER++))
done
