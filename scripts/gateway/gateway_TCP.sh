#!/bin/bash
function check_service {
	  /bin/nc -z ${1} ${2} 2>/dev/null
	    while test $? -eq 1; do
		        echo "wait 10s for service available at ${1}:${2}"
			    sleep 10
				  done
			  }

			  # redirect ouput to /var/log/userdata/log
			  exec > /var/log/userdata.log
			  exec 2>&1

			  # wait until meta data server is available
			  check_service 169.254.169.254 80

			  # get local ip from meta data server
			  LOCALIP=$(curl http://169.254.169.254/latest/meta-data/local-ipv4)
			  LOCALNET=$( echo ${LOCALIP} | cut -f 1-3 -d".")

			  #enable ip forwarding
			  echo "1" > /proc/sys/net/ipv4/ip_forward

			  # Map port number to local ip-address
			  # 30000+x -> LOCALNET.0+x:22
			  # 31000+x -> LOCALNET.0+x:80
			  # 32000+x -> LOCALNET.0+x:443
			  # x > 0 and x < 255


			  #ip forwarding rules
			  for ((n=1; n <=254; n++))
				          {
					   SSH_PORT=$((30000+$n))

					   echo $n

				           iptables -t nat -A PREROUTING -i ens3 -p tcp -m tcp --dport ${SSH_PORT} -j DNAT --to-destination ${LOCALNET}.${n}:22
				           iptables -t nat -A POSTROUTING -d ${LOCALNET}.${n}/32 -p tcp -m tcp --dport 22 -j SNAT --to-source ${LOCALIP}

					  }
