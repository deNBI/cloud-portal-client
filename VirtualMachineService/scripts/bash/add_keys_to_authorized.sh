#!/bin/bash
declare -a keys_to_add=KEYS_TO_ADD
echo "Found keys: ${#keys_to_add[*]}"
for ix in ${!keys_to_add[*]}
do
    printf "\n%s" "${keys_to_add[$ix]}" >> /home/ubuntu/.ssh/authorized_keys

done
