import shlex
import shutil
import sys
from tempfile import NamedTemporaryFile, TemporaryDirectory
import ruamel.yaml
import subprocess


class BiocondaPlaybook(object):

    def __init__(self, ip, port, play_source, osi_private_key, public_key):
        self.ancon_dir = "/code/VirtualMachineService/ancon"
        self.playbooks_dir = self.ancon_dir + "/playbooks"
        self.directory = TemporaryDirectory(dir=self.ancon_dir)
        shutil.copy(self.playbooks_dir+"/bioconda.yml", self.directory.name)
        shutil.copy(self.playbooks_dir+"/variables.yml", self.directory.name)
        self.ip = ip
        self.port = port
        self.private_key = NamedTemporaryFile(mode="w+", dir=self.directory.name, delete=False)
        self.private_key.write(osi_private_key)
        self.private_key.close()

        # create inventory and add the to-be-installed tools to the variables.yml
        self.inventory = NamedTemporaryFile(mode="w+", dir=self.directory.name, delete=False)
        inventory_string = "[vm]\n" + self.ip + ":" + self.port + " ansible_user=ubuntu " \
                                                        "ansible_ssh_private_key_file=" + self.private_key.name
        self.inventory.write(inventory_string)
        self.inventory.close()
        yaml_exec = ruamel.yaml.YAML()
        with open(self.directory.name + "/variables.yml", mode='r+') as variables:
            data = yaml_exec.load(variables)
            data["tools"]["string_line"] = play_source.strip('\"')
            data["tools"]["public_key"] = public_key.strip('\"')
            yaml_exec.dump(data, variables)

    def run_it(self):
        command_string = "/usr/local/bin/ansible-playbook -vvv -i " + self.inventory.name + " " + self.directory.name + "/bioconda.yml"
        command_string = shlex.split(command_string)
        process = subprocess.run(command_string, stdout=sys.stdout, stderr=sys.stderr, universal_newlines=True)
        self.directory.cleanup()
