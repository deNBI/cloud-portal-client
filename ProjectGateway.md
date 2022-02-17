# Project Gateway

The single VM feature of the de.NBI portal allows a registered user to start a virtual machine without having a project located at a specific cloud location. VMs are instantiated in a project associated to the portal. The association between the user and the virtual machine is done and only known by the de.NBI portal.

The started VMs can be accessed using ssh (or any technology on top of it, e.g. x2go). However this needs a public available ip address (floating ip) for each running instance. If we don't have IP addresses available (ipv4 addresses are rare), we have to think of another solution.

A relative simple solution is to create a ssh gateway for the portal project with a fixed mapping between ports and local ip addresses. Linux can be easily configured to act as gateway/router between networks. This linux property is used by a lot of commercial routers.

The tutorial was tested on Ubuntu 16.04 LTS, but should work on any modern linux OS since nothing Ubuntu-specific has been used.

## Assumptions

- portal project with at least one portal user
- full configured project network (router, network/subnet e.g. 192.168.0.0/24)
- one public ip address available (e.g. XX.XX.XX.XX)
- accessible and contiguous port range (e.g. 30000-30255), at least one for each local ip address


## Step by Step

The step by step documentation configures one instance to be ssh gateway for another instance in the same network (192.168.0.0/24).

- **Create a two instance** (192.168.0.10, 192.168.0.11).
- **Associate a floating ip** (XX.XX.XX.XX) to the first instance (192.168.0.10). This instance will be the ssh gateway for the second instance.
- **Login into** the floating ip instance (XX.XX.XX.XX) and enable ip forwarding (as root).

```
echo "1" > /proc/sys/net/ipv4/ip_forward
```


-  **Add nat rules** to allow ip forwarding from *XX.XX.XX.XX:30011* to *192.168.0.11:22*, this can be done using *iptables* (also as root).

```BASH
iptables -t nat -A PREROUTING -i ens3 -p tcp -m tcp --dport 30011 -j DNAT --to-destination 192.168.0.11:22
iptables -t nat -A POSTROUTING -d 192.168.00.11/32 -p tcp -m tcp --dport 22 -j SNAT --to-source 192.168.0.10
```

- **Add a OpenStack security group rule** to allow incoming tcp traffic on port 30011.

- **Login** into the instance (192.168.0.11) is now possible without adding a floating ip.

```BASH
ssh -i my_cloud_key ubuntu@XX.XX.XX.XX -p 30011
```

## Configuration using user data

Configure a project gateway manually is a bit plodding. However, since we have a fixed mapping between ports and local ip addresses, we can automate this step by writing a small script and provide it as user data at instance start. The script should do the following steps :

1. wait for metadata server to be available
2. get the CIDR mask from the metadata service
3. enable ip forwarding
4. add a forwarding rules for ssh (Port 22) for each available ip address (2 ... 254)
5. create a new security group that allows incoming tcp connections from port 30002 to port 30254 and associate it to the gateway instance

The full script could look like the following:

```BASH
#!/bin/bash
function check_service {
  /bin/nc ${1} ${2} </dev/null 2>/dev/null
  while test $? -eq 1; do
    log "wait 10s for service available at ${1}:${2}"
    sleep 10
    /bin/nc ${1} ${2} </dev/null 2>/dev/null
  done
}

# redirect ouput to /var/log/userdata/log
exec > /var/log/gateway.log
exec 2>&1

# wait until meta data server is available
check_service 169.254.169.254 80

# get local ip from meta data server
LOCALIP=$(curl http://169.254.169.254/latest/meta-data/local-ipv4)
LOCALNET=$( echo ${LOCALIP} | cut -f 1-3 -d".")

#enable ip forwarding
echo "1" > /proc/sys/net/ipv4/ip_forward

# Map port number to local ip-address
# 30000+x*3+0 -> LOCALNET.0+x:22
# 30001+x*3+1 -> LOCALNET.0+x:80
# 30002+x*3+2 -> LOCALNET.0+x:443
# x > 0 and x < 255

#ip forwarding rules
for ((n=1; n <=254; n++))
        {
        SSH_PORT=$((30000+$n*3))
        HTTP_PORT=$((30001+$n*3))
        HTTPS_PORT=$((30002+$n*3))

        iptables -t nat -A PREROUTING -i ens3 -p tcp -m tcp --dport ${SSH_PORT} -j DNAT --to-destination ${LOCALNET}.${n}:22
        iptables -t nat -A POSTROUTING -d ${LOCALNET}.${n}/32 -p tcp -m tcp --dport 22 -j SNAT --to-source ${LOCALIP}

        iptables -t nat -A PREROUTING -i ens3 -p tcp -m tcp --dport ${HTTP_PORT} -j DNAT --to-destination ${LOCALNET}.${n}:80
        iptables -t nat -A POSTROUTING -d ${LOCALNET}.${n}/32 -p tcp -m tcp --dport 80 -j SNAT --to-source ${LOCALIP}

        iptables -t nat -A PREROUTING -i ens3 -p tcp -m tcp --dport ${HTTPS_PORT} -j DNAT --to-destination ${LOCALNET}.${n}:443
        iptables -t nat -A POSTROUTING -d ${LOCALNET}.${n}/32 -p tcp -m tcp --dport 443 -j SNAT --to-source ${LOCALIP}
        }
```
