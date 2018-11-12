import os
import click
import yaml
import pprint


@click.command()
def createConfig():
    dir=os.path.dirname(os.path.abspath(__file__))
    filename = dir + '/../config/config.yml'
    host = setHost()
    port = setPort()
    jumphost_base = setJumpHostBase()
    jumphost_ip = setJumpHostIp()
    use_jumphost = setUseJumphost()
    network = setNetwork()
    tag = setTag()
    floating_ip_network = setFloatingIPNetwork()
    certfile = setPathToCertfile()

    click.echo("Creating Config")

    config = dict(openstack_connection=dict(host=host, port=port, jumphost_base=jumphost_base, jumphost_ip=jumphost_ip,
                                            use_jumphost=use_jumphost, network=network, tag=tag
                                            , floating_ip_network=floating_ip_network, certfile=certfile))
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as outfile:
        yaml.dump(config, outfile, default_flow_style=False)

    y = yaml.safe_load(open(filename, 'r'))

    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(y)
    use = None
    while (use != 'y' and use != 'N'):
        use = input('Should this configuration be used: [y/N] ?: ')
        print(use)
    if use == 'y':
        print('Config saved')
        return
    else:
        print('Restarting configuration')
        return createConfig()

def setNetwork():
    network = input('Set the Network for the portal-cloud-client: ')
    return network


def setFloatingIPNetwork():
    network = input('Set the FloatingIpNetwork for the portal-cloud-client: ')
    return network


def setPathToCertfile():
    path = input('Set the path to the certfile: ')
    return path


def setUseJumphost():
    use = None
    while (use != 'y' and use != 'N'):
        use = input('Should the client use the jumphost? [y,N]: ')
    if use == 'y':
        return True
    else:
        return False


def setTag():
    tag = input('Set the tag for the portal-cloud-client: ')
    return tag


def setHost():
    host = input('Set the host for the portal-cloud-client: ')
    return host


def setPort():
    port = input('Set the port for the portal-cloud-client: ')
    return port


def setJumpHostBase():
    jumphost_base = input('Set the jumphost_base for the portal-cloud-client: ')
    return jumphost_base


def setJumpHostIp():
    jumphost_ip = input('Set the jumphost_ip for the portal-cloud-client: ')
    return jumphost_ip


