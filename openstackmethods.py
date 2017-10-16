from openstack import connection

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
        networks=[{"uuid": network.id}], key_name=keypair.name)

        server = conn.compute.wait_for_server(server)

        print("ssh -i {key} root@{ip}".format(
        key=keyname,
        ip=server.access_ipv4))
        meta={'username':username2,}


        networkID = conn.network.find_network('cebitec').id
        floatingIp = conn.network.create_ip(floating_network_id=networkID)
        floatingIp = conn.network.get_ip(floatingIp)
        conn.compute.add_floating_ip_to_server(server, floatingIp.floating_ip_address)

        conn.compute.set_server_metadata(server,**meta)
        print(conn.compute.get_server_metadata(server))
    except Exception as e :
        print("Create_Server_Error: " + e.__str__())
        raise Exception

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
    server = conn.compute.get_server(server)
    if server.status == 'ACTIVE':
        conn.compute.pause_server(server)
        print('paused server' + servername)
        return 'paused server' + servername
    else:
        print('server' + servername + 'was already paused')
        return 'server' + servername + 'was already paused'

def unpause_server(conn, servername):
    server = conn.compute.find_server(servername)
    server = conn.compute.get_server(server)
    if server.status == 'PAUSED':
        conn.compute.unpause_server(server)
        print('unpaused server' + servername)
        return 'unpaused server' + servername
    else:
        print('server' + servername + 'wasnt paused')
        return 'server' + servername + 'wasnt paused'