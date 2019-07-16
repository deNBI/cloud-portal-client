import logging
import shlex
import shutil
import sys
from tempfile import NamedTemporaryFile, TemporaryDirectory
import ruamel.yaml
import subprocess


class BiocondaPlaybook(object):

    def __init__(self, ip, port, play_source, osi_private_key, public_key):
        self.status = -1
        self.stdout = ''
        self.stderr = ''
        # directories and files
        self.ancon_dir = "/code/VirtualMachineService/ancon"
        self.playbooks_dir = self.ancon_dir + "/playbooks"
        self.directory = TemporaryDirectory(dir=self.ancon_dir)
        #self.log_file = NamedTemporaryFile(mode='w+', delete=False, dir=self.directory.name)
        shutil.copy(self.playbooks_dir+"/bioconda.yml", self.directory.name)
        shutil.copy(self.playbooks_dir+"/variables.yml", self.directory.name)
        self.ip = ip
        self.port = port
        self.private_key = NamedTemporaryFile(mode="w+", dir=self.directory.name, delete=False)
        self.private_key.write(osi_private_key)
        self.private_key.close()

        # logging
        #self.logger = logging.getLogger(__name__)
        #self.logger.setLevel(logging.DEBUG)
        # create file handler which logs even debug messages
        #self.fh = logging.FileHandler(self.log_file.name)
        #self.fh.setLevel(logging.DEBUG)
        # create formatter and add it to the handlers
        #self.formatter = logging.Formatter(
        #    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        #)
        #self.fh.setFormatter(self.formatter)
        # add the handlers to the logger
        #self.logger.addHandler(self.fh)

        # create inventory and add the to-be-installed tools to the variables.yml
        self.inventory = NamedTemporaryFile(mode="w+", dir=self.directory.name, delete=False)
        inventory_string = "[vm]\n" + self.ip + ":" + self.port + " ansible_user=ubuntu " \
                                                        "ansible_ssh_private_key_file=" + self.private_key.name
        self.inventory.write(inventory_string)
        self.inventory.close()

        # load variables.yml and change some of its content
        yaml_exec = ruamel.yaml.YAML()
        with open(self.directory.name + "/variables.yml", mode='r') as variables:
            data = yaml_exec.load(variables)
            data["tools"]["string_line"] = play_source.strip('\"')
            data["tools"]["public_key"] = public_key.strip('\"')
            data["tools"]["timeout_length"] = str(len(play_source.split()) * 5) + "m"
        with open(self.directory.name + "/variables.yml", mode='w') as variables:
            yaml_exec.dump(data, variables)

    def run_it(self):
        command_string = "/usr/local/bin/ansible-playbook -v -i {0} {1}/bioconda.yml"\
            .format(self.inventory.name, self.directory.name)
        command_string = shlex.split(command_string)
        process = subprocess.run(command_string, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        # self.logger.log(level=20, msg=process.stdout)
        self.stdout = process.stdout
        if len(process.stderr) > 0:
            self.stderr = process.stderr
            # self.logger.log(level=50, msg=process.stderr)
        self.status = process.returncode
        return process.returncode, process.stdout, process.stderr

    def get_logs(self):
        return self.status, self.stdout, self.stderr

    def cleanup(self):
        self.directory.cleanup()
