import os
import yaml
import pprint
import click

@click.command()
def showConfig():
    dir = os.path.dirname(os.path.abspath(__file__))
    filename = dir + '/../../config/config.yml'
    try:

        y = yaml.safe_load(open(filename, 'r'))
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(y)
    except Exception as e:
        print(e)
        print('No config.yml found. Create one with createConfig')
