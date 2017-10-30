from VirtualMachineService import Iface
from ttypes import VM
from openstack import connection


class VirtualMachineHandler(Iface):


    def create_connection(self, username, password, auth_url, project_name, user_domain_name, project_domain_name):
        conn = connection.Connection(auth_url=auth_url, project_name=project_name, username=username, password=password,
                                     user_domain_name=user_domain_name, project_domain_name=project_domain_name)
        print(conn)
        return conn




    def create_vm(self, flav, img):
        vm = VM( flav, img)
        return vm

    def create_keypair(self, username, password, auth_url, project_name, user_domain_name, project_domain_name, keyname):
        conn=self.create_connection(username=username,password=password,auth_url=auth_url,project_name=project_name,user_domain_name=user_domain_name,project_domain_name=project_domain_name)
        keypair = conn.compute.find_keypair(keyname)

        if not keypair:
            print("Create Key Pair:")
            keypair = conn.compute.create_keypair(name=keyname)
            print(keypair)

        return keypair

    def start_server(self, username, password, auth_url, project_name, user_domain_name, project_domain_name, vm, keyname, servername, network):
        conn = self.create_connection(username=username, password=password, auth_url=auth_url,
                                      project_name=project_name, user_domain_name=user_domain_name,
                                      project_domain_name=project_domain_name)

        image=conn.compute.find_image(vm.img)
        flavor=conn.compute.find_flavor(vm.flav.name)
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

