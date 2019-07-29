import shlex
import shutil
from tempfile import NamedTemporaryFile, TemporaryDirectory
import ruamel.yaml
import subprocess

BIOCONDA = "bioconda"


class Playbook(object):

    def __init__(self, ip, port, playbooks_information, osi_private_key, public_key, logger):
        self.yaml_exec = ruamel.yaml.YAML()
        self.vars_files = []
        self.tasks = []
        self.logger = logger
        # init return logs
        self.status = -1
        self.stdout = ''
        self.stderr = ''
        # init temporary directories and mandatory generic files
        self.ancon_dir = "/code/VirtualMachineService/ancon"  # path to this directory
        self.playbooks_dir = self.ancon_dir + "/playbooks"  # path to source playbooks
        self.directory = TemporaryDirectory(dir=self.ancon_dir)
        self.private_key = NamedTemporaryFile(mode="w+", dir=self.directory.name, delete=False)
        self.private_key.write(osi_private_key)
        self.private_key.close()

        # create the custom playbook and save its name
        self.playbook_exec_name = "generic_playbook.yml"
        self.copy_playbooks_and_init(playbooks_information, public_key)

        # create inventory
        self.inventory = NamedTemporaryFile(mode="w+", dir=self.directory.name, delete=False)
        inventory_string = "[vm]\n" + ip + ":" + port + " ansible_user=ubuntu " \
                                                        "ansible_ssh_private_key_file=" + self.private_key.name
        self.inventory.write(inventory_string)
        self.inventory.close()

    def copy_playbooks_and_init(self, playbooks_information, public_key):
        for k, v in playbooks_information.items():
            self.copy_and_init(k, v)

        # init yml to change public keys as last task
        shutil.copy(self.playbooks_dir + "/change_key.yml", self.directory.name)
        shutil.copy(self.playbooks_dir + "/change_key_vars_file.yml", self.directory.name)
        with open(self.directory.name + "/change_key_vars_file.yml", mode='r') as key_file:
            data_ck = self.yaml_exec.load(key_file)
            data_ck["change_key_vars"]["key"] = public_key.strip('\"')
        with open(self.directory.name + "/change_key_vars_file.yml", mode='w') as key_file:
            self.yaml_exec.dump(data_ck, key_file)
        self.add_to_playbook_lists("change_key")

        # write all vars_files and tasks in generic_playbook
        shutil.copy(self.playbooks_dir + "/" + self.playbook_exec_name, self.directory.name)
        with open(self.directory.name + "/" + self.playbook_exec_name, mode='r') as generic_playbook:
            data_gp = self.yaml_exec.load(generic_playbook)
            data_gp[0]["vars_files"] = self.vars_files
            data_gp[0]["tasks"] = self.tasks
        with open(self.directory.name + "/" + self.playbook_exec_name, mode='w') as generic_playbook:
            self.yaml_exec.dump(data_gp, generic_playbook)

    def copy_and_init(self, playbook_name, playbook_vars):

        def load_vars():
            if playbook_name == BIOCONDA:
                for k, v in playbook_vars.items():
                    if k == "string_line":
                        data[playbook_name + "_tools"][k] = v.strip('\"')
                        data[playbook_name + "_tools"]["timeout_length"] = str(len(v.split()) * 5) + "m"

        playbook_yml = "/{0}.yml".format(playbook_name)
        playbook_var_yml = "/{0}_vars_file.yml".format(playbook_name)
        try:
            shutil.copy(self.playbooks_dir + playbook_yml,
                        self.directory.name)
            try:
                shutil.copy(self.playbooks_dir + playbook_var_yml,
                            self.directory.name)
                with open(self.directory.name + playbook_var_yml, mode='r') as variables:
                    data = self.yaml_exec.load(variables)
                    load_vars()
                with open(self.directory.name + playbook_var_yml, mode='w') as variables:
                    self.yaml_exec.dump(data, variables)
                self.add_to_playbook_lists(playbook_name)
            except shutil.Error as e:
                self.logger.exception(e)
                self.add_tasks_only(playbook_name)
        except shutil.Error as e:
            self.logger.exception(e)

    def add_to_playbook_lists(self, playbook_name):
        self.vars_files.append(playbook_name + "_vars_file.yml")
        self.tasks.append(dict(name="Running {0} tasks".format(playbook_name), import_tasks=playbook_name+".yml"))

    def add_tasks_only(self, playbook_name):
        self.tasks.append(dict(name="Running {0} tasks".format(playbook_name), import_tasks=playbook_name+".yml"))

    def run_it(self):
        command_string = "/usr/local/bin/ansible-playbook -v -i {0} {1}/{2}"\
            .format(self.inventory.name, self.directory.name, self.playbook_exec_name)
        command_string = shlex.split(command_string)
        process = subprocess.run(command_string,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 universal_newlines=True)
        self.stdout = process.stdout
        if len(process.stderr) > 0:
            self.stderr = process.stderr
        self.status = process.returncode
        return process.returncode, process.stdout, process.stderr

    def get_logs(self):
        return self.status, self.stdout, self.stderr

    def cleanup(self):
        self.directory.cleanup()
