"""Script for showing the  configuration for the cloud-portal-client."""
import os
import yaml
import pprint
import click


@click.command()
def showConfig():
    """
    Show configuration.

    :return:
    """
    dir = os.path.dirname(os.path.abspath(__file__))
    filename = dir + '/../../config/config.yml'
    try:

        y = yaml.safe_load(open(filename, 'r'))
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(y)
    except Exception as e:
        print(e)
        print('No config.yml found.\n Create one with portal_client_create_config.')
