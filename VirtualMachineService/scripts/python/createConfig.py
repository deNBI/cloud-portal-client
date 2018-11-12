"""Scripts for creating a configuration for the cloud-portal-client."""
import os
import click
import yaml
import pprint


@click.command()
def createConfig():
    """
    Create config from input params.

    :return:
    """
    dir = os.path.dirname(os.path.abspath(__file__))
    filename = dir + '/../../config/config.yml'
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
                                            use_jumphost=use_jumphost, network=network, tag=tag,
                                            floating_ip_network=floating_ip_network, certfile=certfile))
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
    """
    Set network.

    :return: input network.
    """
    network = input('Set the Network for the portal-cloud-client: ')
    return network


def setFloatingIPNetwork():
    """
    Set floating ip network.

    :return: Input floating ip network
    """
    network = input('Set the FloatingIpNetwork for the portal-cloud-client: ')
    return network


def setPathToCertfile():
    """
    Set Path to Certfile.

    :return: Input path to certfile
    """
    path = input('Set the path to the certfile: ')
    return path


def setUseJumphost():
    """
    Set if jumphost should be used.

    :return: True or False
    """
    use = None
    while (use != 'y' and use != 'N'):
        use = input('Should the client use the jumphost? [y,N]: ')
    if use == 'y':
        return True
    else:
        return False


def setTag():
    """
    Set Tag.

    :return: input tag
    """
    tag = input('Set the tag for the portal-cloud-client: ')
    return tag


def setHost():
    """
    Set Host.

    :return: input host
    """
    host = input('Set the host for the portal-cloud-client: ')
    return host


def setPort():
    """
    Set Port.

    :return: input port
    """
    port = input('Set the port for the portal-cloud-client: ')
    return port


def setJumpHostBase():
    """
    Set Base of Jumphost.

    :return: base jumphost input
    """
    jumphost_base = input('Set the jumphost_base for the portal-cloud-client: ')
    return jumphost_base


def setJumpHostIp():
    """
    Set Ip of Jumphost.

    :return: jumphost_ip input
    """
    jumphost_ip = input('Set the jumphost_ip for the portal-cloud-client: ')
    return jumphost_ip
