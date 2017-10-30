from VirtualMachineService import Iface
from ttypes import VM
from openstack import connection


class VirtualMachineHandler(Iface):


    def create_connection(self, username, password, auth_url, project_name, user_domain_name,
                          project_domain_name):
        conn = connection.Connection(auth_url=auth_url, project_name=project_name, username=username, password=password,
                                     user_domain_name=user_domain_name, project_domain_name=project_domain_name)
        return conn

    def __init__(self, username, password, network, auth_url, project_name, user_domain_name,
                          project_domain_name):
        self.conn=self.create_connection(username, password, auth_url, project_name, user_domain_name,
                          project_domain_name)
        self.network=network


    def create_vm(self, flav, img):
        vm = VM( flav, img)
        return vm

    def create_keypair(self, keyname):
        keypair = self.conn.compute.find_keypair(keyname)

        if not keypair:
            print("Create Key Pair:")
            keypair = self.conn.compute.create_keypair(name=keyname)
            print(keypair)

        return keypair
    def start_server(self, vm,keyname,servername):
        image=self.conn.compute.find_image(vm.img)
        flavor=self.conn.compute.find_flavor(vm.flav.name)
        network=self.conn.network.find_network(self.network)
        keypair=self.create_keypair(keyname)

        try:
            if self.conn.compute.find_server(servername) is not None:
                raise Exception

            server = self.conn.compute.create_server(
                name=servername, image_id=image.id, flavor_id=flavor.id,
                networks=[{"uuid": network.id}], key_name=keypair.name)

            # server = conn.compute.wait_for_server(server)

            return True
        except Exception as e:
            print("Create_Server_Error: " + e.__str__())
            return False

