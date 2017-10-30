from VirtualMachineService import Iface
from ttypes import VM,Flavor
from openstack import connection


class VirtualMachineHandler(Iface):


    def create_connection(self, username, password, auth_url, project_name, user_domain_name, project_domain_name):
        conn = connection.Connection(auth_url=auth_url, project_name=project_name, username=username, password=password,
                                     user_domain_name=user_domain_name, project_domain_name=project_domain_name)
        print(conn)
        return conn


    def get_Flavors(self, username, password, auth_url, project_name, user_domain_name, project_domain_name):
            conn = self.create_connection(username=username, password=password, auth_url=auth_url, project_name=project_name,
                                  user_domain_name=user_domain_name, project_domain_name=project_domain_name)

            flavors=list()
            for flav in conn.compute.flavors():
                flav=flav.to_dict()
                flavor=Flavor(flav['vcpus'],flav['ram'],flav['disk'],flav['name'])
                flavors.append(flavor)
            return flavors
    def create_keypair(self, username, password, auth_url, project_name, user_domain_name, project_domain_name, keyname):
        conn=self.create_connection(username=username,password=password,auth_url=auth_url,project_name=project_name,user_domain_name=user_domain_name,project_domain_name=project_domain_name)
        keypair = conn.compute.find_keypair(keyname)

        if not keypair:
            print("Create Key Pair:")
            keypair = conn.compute.create_keypair(name=keyname)
            print(keypair)

        return keypair

    def start_server(self, username, password, auth_url, project_name, user_domain_name, project_domain_name, flavor, image, keyname, servername, network):
        conn = self.create_connection(username=username, password=password, auth_url=auth_url,
                                      project_name=project_name, user_domain_name=user_domain_name,
                                      project_domain_name=project_domain_name)


        image=conn.compute.find_image(image)
        flavor=conn.compute.find_flavor(flavor.name)
        network=conn.network.find_network(network)
        keypair=self.create_keypair(username, password, auth_url, project_name, user_domain_name, project_domain_name,keyname)

        try:
            if conn.compute.find_server(servername) is not None:
                raise Exception

            server = conn.compute.create_server(
                name=servername, image_id=image.id, flavor_id=flavor.id,
                networks=[{"uuid": network.id}], key_name=keypair.name)

            # server = conn.compute.wait_for_server(server)

            return True
        except Exception as e:
            print("Create_Server_Error: " + e.__str__())
            return False

