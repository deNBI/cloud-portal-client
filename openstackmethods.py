from openstack import connection

import os
def create_connection(username,password):
		conn=connection.Connection(auth_url='https://openstack.cebitec.uni-bielefeld.de:5000/v3/',project_name='PortalClient',username=username,password=password,user_domain_name='default',project_domain_name='default')
		return conn

def create_keypair(conn,keyname):
    keypair = conn.compute.find_keypair(keyname)

    if not keypair:
        print("Create Key Pair:")

        keypair = conn.compute.create_keypair(name='keyname')

        print(keypair)

        try:
            os.mkdir(SSH_DIR)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise e

        with open(PRIVATE_KEYPAIR_FILE, 'w') as f:
            f.write("%s" % keypair.private_key)

        os.chmod(PRIVATE_KEYPAIR_FILE, 0o400)

    return keypair

def create_server(conn,servername,keyname):
    print("Create Server:")

    image = conn.compute.find_image('Ubuntu 14.04 LTS (07/24/17)')
    flavor = conn.compute.find_flavor('unibi.micro')
    network = conn.network.find_network('portalnetzwerk')
    keypair = create_keypair(conn,keyname)
    try:
        serverexist=conn.compute.find_server(servername)

        server = conn.compute.create_server(
        name=servername, image_id=image.id, flavor_id=flavor.id,
        networks=[{"uuid": network.id}], key_name=keypair.name)

        server = conn.compute.wait_for_server(server)

        print("ssh -i {key} root@{ip}".format(
        key=keyname,
        ip=server.access_ipv4))


    except Exception :
        print("erroroccured")
        raise Exception

def delete_server(conn,servername):
		print("Delete Server")
		server=conn.compute.find_server(servername)
		print(server)
		conn.compute.delete_server(server)

def stop_server(conn,servername):
    server = conn.compute.find_server(servername)
    conn.compute.stop_server(server)
    print("Stopped Server " + servername)