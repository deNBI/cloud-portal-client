import shlex
import shutil
import sys
from tempfile import NamedTemporaryFile, TemporaryDirectory
import ruamel.yaml
import subprocess


class BiocondaPlaybook(object):

    def __init__(self, ip, port, play_source):
        self.ancon_dir = "/code/VirtualMachineService/ancon"
        self.playbooks_dir = self.ancon_dir + "/playbooks"
        self.directory = TemporaryDirectory(dir=self.ancon_dir)
        shutil.copy(self.playbooks_dir+"/bioconda.yml", self.directory.name)
        shutil.copy(self.playbooks_dir+"/variables.yml", self.directory.name)
        self.ip = ip
        self.port = port
        self.private_key = NamedTemporaryFile(mode="w+", dir=self.directory.name, delete=False)
        self.private_key.write("""-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAvO3PMJojazQj1XljbTph404C74oQR3qRsWzhUyBERVlRsdJi
Wv0i+LPOmFKDyZ5e7c5YHoPaqItgfc4L49f+v0TcwYyAJth85jv6VF4qz+hEzmi5
GlR3IXmUCk8JuyuU+o6oHqxr8RD3lBT76Lwu2FIN5OqXZlMMDwzkWex/8rrFVGyM
JL1OSpnt6pspPdp7Nlxy7rakSprfalqhRlK0BWf/jkVx+VZwMQVZNNUlLaDIAzyO
03aEbnCAZVG+6OXbr9hZwwZ9WY+XfA013uGandntQQdShdop/nm6NirUyQE9gtzM
omeoGt+u/YK1/2MbOouUlx2aEXkFWIJWrZd6owIDAQABAoIBAQCmP0jzRp9mJVJm
9dMk+ZvLjgkNSds7WsK7csjwAdOxhoBZznxX/qn4WRixduKa1u5HqixmZbZSW5sD
+P0DeDyliG4NLppSFGwLmLmV5escWhG54/MGFU9jOH2peJVii14kAMY1f5nYXgrN
1o045eb+2W16g2fIVcmlsL17151bM7WD5p+Jsm6zxIR23pV+NAgY6rt/Kdy+y5O1
rh+oQrwEx0+k5ig6DIRkfgBvAKwreqaaPRHMryxOOR/CRxB6zLyoyatCEjCWDLcl
cii0Zz95c6msHVBeZ4x2HeRulitLdvD9f4oYaojw277wg3mBDMWq2GZMc7xHl+6f
14cAsp0BAoGBAN2yXd9VH5ptiEwi8aKqc6RxPwiofCjnkfwAUiBeiHKbSMidnDDp
+N4Azt1KFCIMWWTkxr/h1LHbhTBdJrLyR+HKHQ9qyJrqm3vNmk0WYW6PiX5LdlHL
cKaRlyfjt7BGfjBetnrapcPuxQEQ1VIRZgXTaY5MIhrXgsUYH/GFyLSBAoGBANop
egmuOHm0pk+DJyfivozhhYmWoNlA8x3aqdnZuseMonpLROBEtQrF0YsHHFHiRUvG
K/6RYzVudpKSmB8grmmGmYNMwppD9ZJ55+/1cnFCQFmU1oENH1GDZhLmNTeinDXV
LgFhCH+bR3Lp/6kdlEpXVXE9sinue4V/me3m3E0jAoGAKoj0VcshOyHUyrbRoaIO
efh4XZLl73sumSj+mNNKXqLIfiUvOHtLklyZU//IiRfRdvgl4d7UTiOOFE9rA15U
yE9c7/5O6tokZsZ12mB25R2JBcA4vUzJGkxIshCQx7Netq0VWdDliQggqCmwpARO
jMOZNwIIcRn0LxiH2HEQpwECgYEAzzvDD1sNjp7JtJITKdI7y7uWjAInvPfzeRJz
cdtfj5rJ5H2Haboad6c9y2Dvx+C2jqoqtGEK6oCJ5eWW10rGIruXK6BI4x1XMtLW
PZzcHzYdxnqZ4HDEpTu6RI2lU7oFxSVB1FGGLyEjl8cr8kuEx7F6Gl3O1gISF9gE
MnawIh0CgYBSmrR8kHDkHLWbPkKhH93qrJxbo0vSsk+F77Zb+0jA5yLk4SK8jhcx
/p8iKdiMxnfR6BZyBUYMMW6AXx0Wg+iRQflka+/ugJUFyvELPm2s4ENRY68pTLj8
Zc+swBO6T87o29E6e4NLDtQ+h9MsoImfKOLRNKSZttOzfjW3MXqRMg==
-----END RSA PRIVATE KEY-----""")
        self.private_key.close()

        # create inventory and add the to-be-installed tools to the variables.yml
        self.inventory = NamedTemporaryFile(mode="w+", dir=self.directory.name, delete=False)
        inventory_string = "[vm]\n" + self.ip + ":" + self.port + " ansible_user=ubuntu " \
                                                        "ansible_ssh_private_key_file=" + self.private_key.name
        self.inventory.write(inventory_string)
        self.inventory.close()
        yaml_exec = ruamel.yaml.YAML()
        self.play_source = play_source.strip('\"')
        with open(self.directory.name + "/variables.yml", mode='r+') as variables:
            data = yaml_exec.load(variables)
            data["tools"]["string_line"] = play_source
            yaml_exec.dump(data, variables)

    def run_it(self):
        command_string = "/usr/local/bin/ansible-playbook -i " + self.inventory.name + " " + self.directory.name + "/bioconda.yml"
        command_string = shlex.split(command_string)
        process = subprocess.run(command_string, stdout=sys.stdout, stderr=sys.stderr, universal_newlines=True)
        self.directory.cleanup()
