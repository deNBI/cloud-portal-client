#!/bin/bash

# get local ip from meta data server
LOCALIP=$(curl http://169.254.169.254/latest/meta-data/local-ipv4)
LOCALNET=$( echo ${LOCALIP} | cut -f 1-3 -d".")

#ip forwarding rules
for ((n=1; n <=254; n++))
        {
        MOSH_BASE=$((30000+$n*10))

        for ((m=0; m<=9; m++))
                {
                        MOSH_PORT=$(($MOSH_BASE+$m))
                        #$echo ${MOSH_PORT}
                        iptables -t nat -A PREROUTING -i ens3 -p udp -m udp --dport ${MOSH_PORT} -j DNAT --to-destination ${LOCALNET}.${n}:${MOSH_PORT}
                        iptables -t nat -A POSTROUTING -d ${LOCALNET}.${n}/32 -p udp -m udp --dport ${MOSH_PORT} -j SNAT --to-source ${LOCALIP}
                }

        }
