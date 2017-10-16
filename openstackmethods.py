from openstack import connection
import json
def create_connection(username,password):
    conn=connection.Connection(auth_url='https://openstack.cebitec.uni-bielefeld.de:5000/v3/',project_name='PortalClient',username=username,password=password,user_domain_name='default',project_domain_name='default')
    return conn

def create_keypair(conn,keyname):
    keypair = conn.compute.find_keypair(keyname)

    if not keypair:
        print("Create Key Pair:")
        keypair = conn.compute.create_keypair(name=keyname)
        print(keypair)



    return keypair

def create_server(conn,username2,servername,keyname):
    print("Create Server:")

    image = conn.compute.find_image('Ubuntu 14.04 LTS (07/24/17)')
    flavor = conn.compute.find_flavor('unibi.micro')
    network = conn.network.find_network('portalnetzwerk')
    keypair = create_keypair(conn,keyname)

    try:
        if   conn.compute.find_server(servername) is not None:
            raise Exception

        server = conn.compute.create_server(
        name=servername, image_id=image.id, flavor_id=flavor.id,
        networks=[{"uuid": network.id}], key_name=keypair.name,metadata={'username':username2,})

        #server = conn.compute.wait_for_server(server)

        print("ssh -i {key} root@{ip}".format(
        key=keyname,
        ip=server.access_ipv4))



    except Exception as e :
        print("Create_Server_Error: " + e.__str__())
        raise Exception

def add_floating_ip_to_server(conn,servername):

    server = conn.compute.find_server(servername)
    if server is None:
        return ('Server ' + servername + ' not found')
    server = conn.compute.get_server(server)
    print("Checking if Server already got an Floating IP")
    for values in server.addresses.values():
        for address in values:
            if address['OS-EXT-IPS:type'] == 'floating':
                return ('Server ' + servername + ' already got an Floating IP ' + address['addr'])
    print("Checking if unused Floating IP exist")
    for floating_ip in conn.network.ips():
        if not floating_ip.fixed_ip_address:
            conn.compute.add_floating_ip_to_server(server,floating_ip.floating_ip_address)
            print("Adding existing Floating IP " + str(floating_ip.floating_ip_address)+  "to  " + servername)
            return  'Added existing Floating IP ' + str(floating_ip.floating_ip_address) +" to Server " +servername
    print("Adding Floating IP to  " + servername)

    networkID = conn.network.find_network('cebitec').id
    floating_ip = conn.network.create_ip(floating_network_id=networkID)
    floating_ip = conn.network.get_ip(floating_ip)
    conn.compute.add_floating_ip_to_server(server, floating_ip.floating_ip_address)
    return 'Added new Floating IP' + floating_ip +" to Server" +servername

def delete_server(conn,servername):
		print("Delete Server")
		server=conn.compute.find_server(servername)
		print(server)
		conn.compute.delete_server(server)

def stop_server(conn,servername):
        server = conn.compute.find_server(servername)
        if server is None:
            return ('Server ' + servername + ' not found')
        server=conn.compute.get_server(server)
        print(server.status)
        #print(conn.compute._get_base_resource(server,_server.Server))
       # res=conn.compute._get_base_resource(server,_server.Server)
        #print(res.status)


        if server.status == 'ACTIVE':
            conn.compute.stop_server(server)
            print("Stopped Server " + servername)
            return "Stopped Server " + servername
        else:
            print('Server ' + servername + ' was already stopped')
            return 'Server ' + servername + ' was already stopped'

def pause_server(conn, servername):
    server = conn.compute.find_server(servername)
    if server is None:
        return json.loads('{"server":"' + servername + '","status":"NOTFOUND"}')
    server = conn.compute.get_server(server)
    status = server.status
    if status == 'ACTIVE':
        conn.compute.pause_server(server)
        return json.loads('{"server":"' + servername + '","status":"PAUSED}')

    elif status == 'PAUSED':
        return json.loads('{"server":"' + servername + '","status":"PAUSED"}')
    else:
        return json.loads('{"server":"' + servername + '","status":"TODO"}')
def unpause_server(conn, servername):
    server = conn.compute.find_server(servername)
    if server is None:
        return json.loads('{"server":"' + servername + '","status":"NOTFOUND"}')
    server = conn.compute.get_server(server)
    status=server.status
    if status=='ACTIVE':
        return json.loads('{"server":"'+servername + '","status":"ACTIVE"}')
    elif status == 'PAUSED':
        conn.compute.unpause_server(server)
        return   json.loads('{"server":"'+servername + '","status":"ACTIVE"}')
    else:
        return  json.loads('{"server":"'+servername + '","status":"TODO"}')