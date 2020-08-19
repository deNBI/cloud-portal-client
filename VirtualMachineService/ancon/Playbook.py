import logging
import shlex
import shutil
import subprocess
from tempfile import NamedTemporaryFile, TemporaryDirectory

import redis
import ruamel.yaml

BIOCONDA = "bioconda"
THEIA = "theiaide"
RSTUDIO = "rstudio"
GUACAMOLE = "guacamole"
JUPYTERNOTEBOOK = "jupyternotebook"
OPTIONAL = "optional"
MOSH = "mosh"

ALL_TEMPLATES = [BIOCONDA, THEIA, RSTUDIO, GUACAMOLE, JUPYTERNOTEBOOK]

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
fh = logging.FileHandler("log/portal_client_debug.log")
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(funcName)s  - %(levelname)s - %(message)s"
)
fh.setFormatter(formatter)
ch.setFormatter(formatter)
LOG.addHandler(fh)
LOG.addHandler(ch)


class Playbook(object):

    ACTIVE = "ACTIVE"
    PLAYBOOK_FAILED = "PLAYBOOK_FAILED"

    def __init__(
        self, ip, port, playbooks_information, osi_private_key, public_key, pool
    ):
        self.redis = redis.Redis(connection_pool=pool)  # redis connection
        self.yaml_exec = ruamel.yaml.YAML()  # yaml writer/reader
        self.vars_files = []  # _vars_file.yml to read
        self.tasks = []  # task list
        self.always_tasks = []
        self.process = (
            None  # init process, returncode, standard output, standard error output
        )
        self.returncode = -1
        self.stdout = ""
        self.stderr = ""
        # init temporary directories and mandatory generic files
        self.ancon_dir = "/code/VirtualMachineService/ancon"  # path to this directory
        self.playbooks_dir = self.ancon_dir + "/playbooks"  # path to source playbooks
        self.directory = TemporaryDirectory(dir=self.ancon_dir)
        self.private_key = NamedTemporaryFile(
            mode="w+", dir=self.directory.name, delete=False
        )
        self.private_key.write(osi_private_key)
        self.private_key.close()

        self.log_file_stdout = NamedTemporaryFile(
            mode="w+", dir=self.directory.name, delete=False
        )
        self.log_file_stderr = NamedTemporaryFile(
            mode="w+", dir=self.directory.name, delete=False
        )

        # create the custom playbook and save its name
        self.playbook_exec_name = "generic_playbook.yml"
        self.copy_playbooks_and_init(playbooks_information, public_key)

        # create inventory
        self.inventory = NamedTemporaryFile(
            mode="w+", dir=self.directory.name, delete=False
        )

        inventory_string = (
            "[vm]\n" + ip + ":" + port + " ansible_user=ubuntu "
            "ansible_ssh_private_key_file="
            + self.private_key.name
            + " ansible_python_interpreter=/usr/bin/python3"
        )
        self.inventory.write(inventory_string)
        self.inventory.close()

    def copy_playbooks_and_init(self, playbooks_information, public_key):
        # go through every wanted playbook
        for k, v in playbooks_information.items():
            self.copy_and_init(k, v)

        # init yml to change public keys as last task
        shutil.copy(self.playbooks_dir + "/change_key.yml", self.directory.name)
        shutil.copy(
            self.playbooks_dir + "/change_key_vars_file.yml", self.directory.name
        )
        with open(
            self.directory.name + "/change_key_vars_file.yml", mode="r"
        ) as key_file:
            data_ck = self.yaml_exec.load(key_file)
            data_ck["change_key_vars"]["key"] = public_key.strip('"')
        with open(
            self.directory.name + "/change_key_vars_file.yml", mode="w"
        ) as key_file:
            self.yaml_exec.dump(data_ck, key_file)
        self.add_to_playbook_always_lists("change_key")

        # write all vars_files and tasks in generic_playbook
        shutil.copy(
            self.playbooks_dir + "/" + self.playbook_exec_name, self.directory.name
        )
        with open(
            self.directory.name + "/" + self.playbook_exec_name, mode="r"
        ) as generic_playbook:
            data_gp = self.yaml_exec.load(generic_playbook)
            data_gp[0]["vars_files"] = self.vars_files
            data_gp[0]["tasks"][0]["block"] = self.tasks
            data_gp[0]["tasks"][0]["always"] = self.always_tasks
        with open(
            self.directory.name + "/" + self.playbook_exec_name, mode="w"
        ) as generic_playbook:
            self.yaml_exec.dump(data_gp, generic_playbook)

    def copy_and_init(self, playbook_name, playbook_vars):
        def load_vars():
            if playbook_name == BIOCONDA:
                for k, v in playbook_vars.items():
                    if k == "packages":
                        p_array = []
                        p_dict = {}
                        for p in (v.strip('"')).split():
                            p_array.append(p.split("="))
                        for p in p_array:
                            p_dict.update({p[0]: {"version": p[1], "build": p[2]}})
                        data[playbook_name + "_tools"][k] = p_dict
            if playbook_name == THEIA:
                for k, v in playbook_vars.items():
                    if k == "template_version":
                        data[playbook_name + "_vars"][k] = v
                    if k == "create_only_backend":
                        data[playbook_name + "_vars"][k] = v
            if playbook_name == RSTUDIO:
                for k, v in playbook_vars.items():
                    if k == "template_version":
                        data[playbook_name + "_vars"][k] = v
                    if k == "create_only_backend":
                        data[playbook_name + "_vars"][k] = v
            if playbook_name == GUACAMOLE:
                for k, v in playbook_vars.items():
                    if k == "template_version":
                        data[playbook_name + "_vars"][k] = v
                    if k == "create_only_backend":
                        data[playbook_name + "_vars"][k] = v
            if playbook_name == OPTIONAL:
                for k, v in playbook_vars.items():
                    if k == MOSH:
                        data[playbook_name + "_defined"][k] = v

        playbook_yml = "/{0}.yml".format(playbook_name)
        playbook_var_yml = "/{0}_vars_file.yml".format(playbook_name)
        try:
            shutil.copy(self.playbooks_dir + playbook_yml, self.directory.name)
            try:
                shutil.copy(self.playbooks_dir + playbook_var_yml, self.directory.name)
                with open(
                    self.directory.name + playbook_var_yml, mode="r"
                ) as variables:
                    data = self.yaml_exec.load(variables)
                    load_vars()
                with open(
                    self.directory.name + playbook_var_yml, mode="w"
                ) as variables:
                    self.yaml_exec.dump(data, variables)
                self.add_to_playbook_lists(playbook_name)
            except shutil.Error as e:
                LOG.exception(e)
                self.add_tasks_only(playbook_name)
            except IOError as e:
                LOG.exception(e)
                self.add_tasks_only(playbook_name)
        except shutil.Error as e:
            LOG.exception(e)
        except IOError as e:
            LOG.exception(e)

    def add_to_playbook_lists(self, playbook_name):
        self.vars_files.append(playbook_name + "_vars_file.yml")
        self.tasks.append(
            dict(
                name="Running {0} tasks".format(playbook_name),
                import_tasks=playbook_name + ".yml",
            )
        )

    def add_tasks_only(self, playbook_name):
        self.tasks.append(
            dict(
                name="Running {0} tasks".format(playbook_name),
                import_tasks=playbook_name + ".yml",
            )
        )

    def add_to_playbook_always_lists(self, playbook_name):
        self.vars_files.append(playbook_name + "_vars_file.yml")
        self.always_tasks.append(
            dict(
                name="Running {0} tasks".format(playbook_name),
                import_tasks=playbook_name + ".yml",
            )
        )

    def add_always_tasks_only(self, playbook_name):
        self.always_tasks.append(
            dict(
                name="Running {0} tasks".format(playbook_name),
                import_tasks=playbook_name + ".yml",
            )
        )

    def run_it(self):
        command_string = "/usr/local/bin/ansible-playbook -v -i {0} {1}/{2}".format(
            self.inventory.name, self.directory.name, self.playbook_exec_name
        )
        command_string = shlex.split(command_string)
        self.process = subprocess.Popen(
            command_string,
            stdout=self.log_file_stdout,
            stderr=self.log_file_stderr,
            universal_newlines=True,
        )

    def check_status(self, openstack_id):
        done = self.process.poll()
        if done is None:
            LOG.info(
                "Playbook for (openstack_id) {0} still in progress.".format(
                    openstack_id
                )
            )
        elif done != 0:
            LOG.info("Playbook for (openstack_id) {0} has failed.".format(openstack_id))
            self.redis.hset(openstack_id, "status", self.PLAYBOOK_FAILED)
            self.returncode = self.process.returncode
            self.process.wait()
        else:
            LOG.info(
                "Playbook for (openstack_id) {0} is successful.".format(openstack_id)
            )
            self.redis.hset(openstack_id, "status", self.ACTIVE)
            self.returncode = self.process.returncode
            self.process.wait()
        return done

    def get_logs(self):
        self.log_file_stdout.seek(0, 0)
        lines_stdout = self.log_file_stdout.readlines()
        for line in lines_stdout:
            self.stdout += line
        self.log_file_stderr.seek(0, 0)
        line_stderr = self.log_file_stderr.readlines()
        for line in line_stderr:
            self.stderr += line
        return self.returncode, self.stdout, self.stderr

    def cleanup(self, openstack_id):
        self.directory.cleanup()
        self.redis.delete(openstack_id)

    def stop(self, openstack_id):
        self.process.terminate()
        rc, stdout, stderr = self.get_logs()
        logs_to_save = {"returncode": rc, "stdout": stdout, "stderr": stderr}
        self.redis.hmset("pb_logs_{0}".format(openstack_id), logs_to_save)
        self.cleanup(openstack_id)
