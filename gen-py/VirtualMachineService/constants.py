#
# Autogenerated by Thrift Compiler (0.10.0)
#
# DO NOT EDIT UNLESS YOU ARE SURE THAT YOU KNOW WHAT YOU ARE DOING
#
#  options string: py
#

from thrift.Thrift import TType, TMessageType, TFrozenDict, TException, TApplicationException
from thrift.protocol.TProtocol import TProtocolException
import sys
from ttypes import *
FLAVOR_LIST = [
    Flavor(**{
        "name": "de.NBI.large",
        "vcpus": 32,
        "disk": 20,
        "ram": 64,
    }),
    Flavor(**{
        "ram": 2,
        "disk": 25,
        "name": "BiBiGrid Debug",
        "vcpus": 2,
    }),
    Flavor(**{
        "vcpus": 2,
        "disk": 40,
        "ram": 2,
        "name": "unibi.mirco",
    }),
    Flavor(**{
        "vcpus": 8,
        "ram": 16,
        "disk": 70,
        "name": "unibi.small",
    }),
    Flavor(**{
        "vcpus": 16,
        "ram": 32,
        "disk": 120,
        "name": "unibi.medium",
    }),
    Flavor(**{
        "vcpus": 32,
        "ram": 64,
        "disk": 220,
        "name": "unibi.large",
    }),
    Flavor(**{
        "name": "de.NBI.medium",
        "vcpus": 16,
        "ram": 32,
        "disk": 20,
    }),
    Flavor(**{
        "name": "de.NBI.default",
        "disk": 20,
        "vcpus": 2,
        "ram": 2,
    }),
    Flavor(**{
        "vcpus": 8,
        "disk": 20,
        "ram": 16,
        "name": "de.NBI.small",
    }),
    Flavor(**{
        "name": "unibi.tiny",
        "ram": 8,
        "disk": 70,
        "vcpus": 4,
    }),
]
IMAGES_LIST = [
    "Ubuntu 14.04 LTS (07/24/17)",
    "cirros",
    "BiBiGrid slave 14.04 (06/20/17)",
    "BiBiGrid master 14.04 (08/02/17)",
    "BiBiGrid slave 14.04 (08/01/17)",
    "Ubuntu 16.04 LTS (07/24/17)",
    "BiBiGrid master 14.04 (06/20/17)",
]
