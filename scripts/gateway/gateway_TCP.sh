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
			  LOCALNET=$( echo ${LOCALIP} | cut -f 1-2 -d".")

			  #enable ip forwarding
			  echo "1" > /proc/sys/net/ipv4/ip_forward

      	for ((base=0; base <=8; base++))
      			  {
      			    			  for ((n=1; n <=254; n++))
				          {
					   SSH_PORT=$((30000+$n + base *256))

					   echo $n
					   echo $SSH_PORT

				           iptables -t nat -A PREROUTING -i ens3 -p tcp -m tcp --dport ${SSH_PORT} -j DNAT --to-destination ${LOCALNET}.${base}.${n}:22
				           iptables -t nat -A POSTROUTING -d ${LOCALNET}.${base}.${n}/32 -p tcp -m tcp --dport 22 -j SNAT --to-source ${LOCALIP}

					  }


      			  }


			  #ip forwarding rules

