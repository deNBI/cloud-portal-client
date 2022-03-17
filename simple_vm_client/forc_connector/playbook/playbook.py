import os
import shlex
import shutil
import subprocess
from tempfile import NamedTemporaryFile, TemporaryDirectory

import redis
import ruamel.yaml
from ttypes import CondaPackage
from util.logger import setup_custom_logger
from util.state_enums import VmTaskStates

BIOCONDA = "bioconda"
OPTIONAL = "optional"
MOSH = "mosh"

logger = setup_custom_logger(__name__)


class Playbook(object):
    def __init__(
        self,
        ip: str,
        port: int,
        research_environment_template: str,
        research_environment_template_version: str,
        create_only_backend: bool,
        conda_packages: list[CondaPackage],
        osi_private_key: str,
        public_key: str,
        pool: redis.ConnectionPool,
        loaded_metadata_keys: list[str],
        cloud_site: str,
    ):
        self.loaded_metadata_keys = loaded_metadata_keys
        self.cloud_site: str = cloud_site
        self.redis: redis.Redis = redis.Redis(connection_pool=pool)  # redis connection
        self.yaml_exec = ruamel.yaml.YAML()  # yaml writer/reader
        self.vars_files: list[str] = []  # _vars_file.yml to read
        self.tasks: list[dict[str, str]] = []  # task list
        self.always_tasks: list[dict[str, str]] = []
        self.conda_packages = conda_packages
        self.process: subprocess.Popen = None  # type: ignore
        self.research_environment_template_version = (
            research_environment_template_version
        )
        self.create_only_backend = create_only_backend
        self.returncode: int = -1
        self.stdout: str = ""
        self.stderr: str = ""
        self.research_environment_template = research_environment_template
        # init temporary directories and mandatory generic files
        from forc_connector.template.template import Template

        self.playbooks_dir: str = Template.get_playbook_dir()
        self.directory: TemporaryDirectory = TemporaryDirectory(
            dir=f"{self.playbooks_dir}"
        )
        self.private_key = NamedTemporaryFile(
            mode="w+", dir=self.directory.name, delete=False, prefix="private_key_"
        )
        self.private_key.write(osi_private_key)
        self.private_key.close()

        self.log_file_stdout = NamedTemporaryFile(
            mode="w+", dir=self.directory.name, delete=False, prefix="log_stdout_"
        )
        self.log_file_stderr = NamedTemporaryFile(
            mode="w+", dir=self.directory.name, delete=False, prefix="log_stderr_"
        )

        # create the custom playbook and save its name
        self.playbook_exec_name: str = "generic_playbook.yml"
        self.copy_playbooks_and_init(public_key)

        # create inventory
        self.inventory = NamedTemporaryFile(
            mode="w+", dir=self.directory.name, delete=False, prefix="inventory_"
        )

        inventory_string = (
            f"[vm]\n{ip}:{str(port)} ansible_user=ubuntu "
            f"ansible_ssh_private_key_file={self.private_key.name} "
            f"ansible_python_interpreter=/usr/bin/python3"
        )
        self.inventory.write(inventory_string)
        self.inventory.close()

    def copy_playbooks_and_init(self, public_key: str) -> None:
        # go through every wanted playbook
        # start with conda packages
        self.copy_and_init_conda_packages()
        self.copy_and_init_research_environment()

        # for k, v in playbooks_information.items():
        #    self.copy_and_init(k, v)

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

    def copy_and_init_research_environment(self) -> None:
        if not self.research_environment_template:
            pass
        site_specific_yml = (
            f"/{self.research_environment_template}{'-' + self.cloud_site}.yml"
        )
        playbook_name_local = self.research_environment_template
        if os.path.isfile(self.playbooks_dir + site_specific_yml):
            playbook_name_local = (
                self.research_environment_template + "-" + self.cloud_site
            )
        playbook_yml = f"/{playbook_name_local}.yml"
        playbook_var_yml = f"/{self.research_environment_template}_vars_file.yml"
        try:
            shutil.copy(self.playbooks_dir + playbook_yml, self.directory.name)
            try:
                shutil.copy(self.playbooks_dir + playbook_var_yml, self.directory.name)
                with open(
                    self.directory.name + playbook_var_yml, mode="r"
                ) as variables:
                    data = self.yaml_exec.load(variables)

                    data[self.research_environment_template + "_vars"][
                        "template_version"
                    ] = self.research_environment_template_version
                    data[self.research_environment_template + "_vars"][
                        "create_only_backend"
                    ] = str(self.create_only_backend).lower()
                    with open(
                        self.directory.name + playbook_var_yml, mode="w"
                    ) as variables:
                        self.yaml_exec.dump(data, variables)
                    self.add_to_playbook_lists(
                        playbook_name_local, self.research_environment_template
                    )
            except shutil.Error as e:
                logger.exception(e)
                self.add_tasks_only(playbook_name_local)
            except IOError as e:
                logger.exception(e)
                self.add_tasks_only(playbook_name_local)
        except shutil.Error as e:
            logger.exception(e)
        except IOError as e:
            logger.exception(e)

    def copy_and_init_conda_packages(self) -> None:
        if not self.conda_packages:
            pass
        site_specific_yml = f"/{BIOCONDA}{'-' + self.cloud_site}.yml"
        playbook_name_local = BIOCONDA
        if os.path.isfile(self.playbooks_dir + site_specific_yml):
            playbook_name_local = BIOCONDA + "-" + self.cloud_site
        playbook_yml = f"/{playbook_name_local}.yml"
        playbook_var_yml = f"/{BIOCONDA}_vars_file.yml"
        try:
            shutil.copy(self.playbooks_dir + playbook_yml, self.directory.name)
            try:
                shutil.copy(self.playbooks_dir + playbook_var_yml, self.directory.name)
                with open(
                    self.directory.name + playbook_var_yml, mode="r"
                ) as variables:
                    data = self.yaml_exec.load(variables)
                    p_dict = {}

                    for conda_package in self.conda_packages:
                        p_dict.update(
                            {
                                conda_package.name: {
                                    "version": conda_package.version,
                                    "build": conda_package.build,
                                }
                            }
                        )
                        data[BIOCONDA + "_tools"]["packages"] = p_dict
                        with open(
                            self.directory.name + playbook_var_yml, mode="w"
                        ) as variables:
                            self.yaml_exec.dump(data, variables)
                        self.add_to_playbook_lists(playbook_name_local, BIOCONDA)
            except shutil.Error as e:
                logger.exception(e)
                self.add_tasks_only(playbook_name_local)
            except IOError as e:
                logger.exception(e)
                self.add_tasks_only(playbook_name_local)
        except shutil.Error as e:
            logger.exception(e)
        except IOError as e:
            logger.exception(e)

    def add_to_playbook_lists(
        self, playbook_name_local: str, playbook_name: str
    ) -> None:
        self.vars_files.append(playbook_name + "_vars_file.yml")
        self.tasks.append(
            dict(
                name=f"Running {playbook_name_local} tasks",
                import_tasks=playbook_name_local + ".yml",
            )
        )
        logger.info(
            "Added playbook: "
            + playbook_name_local
            + ".yml"
            + ", vars file: "
            + playbook_name
            + "_vars_file.yml"
        )

    def add_tasks_only(self, playbook_name: str) -> None:
        self.tasks.append(
            dict(
                name=f"Running {playbook_name} tasks",
                import_tasks=playbook_name + ".yml",
            )
        )

    def add_to_playbook_always_lists(self, playbook_name: str) -> None:
        self.vars_files.append(playbook_name + "_vars_file.yml")
        self.always_tasks.append(
            dict(
                name=f"Running {playbook_name} tasks",
                import_tasks=playbook_name + ".yml",
            )
        )

    def add_always_tasks_only(self, playbook_name: str) -> None:
        self.always_tasks.append(
            dict(
                name=f"Running {playbook_name} tasks",
                import_tasks=playbook_name + ".yml",
            )
        )

    def run_it(self) -> None:
        command_string = f"/usr/local/bin/ansible-playbook -v -i {self.inventory.name} {self.directory.name}/{self.playbook_exec_name}"
        command_string = shlex.split(command_string)  # type: ignore
        logger.info(f"Run Playbook for {self.playbook_exec_name} - [{command_string}]")
        self.process = subprocess.Popen(
            command_string,
            stdout=self.log_file_stdout,
            stderr=self.log_file_stderr,
            universal_newlines=True,
        )

    def check_status(self, openstack_id: str) -> int:
        logger.info(f"Check Status Playbook for VM {openstack_id}")
        done = self.process.poll()
        logger.info(f" Status Playbook for VM {openstack_id}: {done}")

        if done is None:
            logger.info(
                f"Playbook for (openstack_id) {openstack_id} still in progress."
            )
            return 3
        elif done != 0:
            logger.info(f"Playbook for (openstack_id) {openstack_id} has failed.")
            self.redis.hset(openstack_id, "status", VmTaskStates.PLAYBOOK_FAILED.value)
            self.returncode = self.process.returncode
            self.process.wait()
        else:
            logger.info(f"Playbook for (openstack_id) {openstack_id} is successful.")
            self.redis.hset(
                openstack_id, "status", VmTaskStates.PLAYBOOK_SUCCESSFUL.value
            )
            self.returncode = self.process.returncode
            self.process.wait()
        return done

    def get_logs(self) -> tuple[int, str, str]:
        self.log_file_stdout.seek(0, 0)
        lines_stdout = self.log_file_stdout.readlines()
        for line in lines_stdout:
            self.stdout += line
        self.log_file_stderr.seek(0, 0)
        line_stderr = self.log_file_stderr.readlines()
        for line in line_stderr:
            self.stderr += line
        return self.returncode, self.stdout, self.stderr

    def cleanup(self, openstack_id: str) -> None:
        self.directory.cleanup()
        self.redis.delete(openstack_id)

    def stop(self, openstack_id: str) -> None:
        self.process.terminate()
        rc, stdout, stderr = self.get_logs()
        logs_to_save = {"returncode": rc, "stdout": stdout, "stderr": stderr}
        self.redis.hset(name=f"pb_logs_{openstack_id}", mapping=logs_to_save)  # type: ignore
        self.cleanup(openstack_id)
