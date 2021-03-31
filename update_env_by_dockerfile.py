#!/usr/bin/python
import fileinput
import sys

DOCKERFILE = sys.argv[1]
ENV_FILE = sys.argv[2]

update_env = {}
with open(DOCKERFILE) as f:
    for line in f:
        vars = line.replace("FROM", "").strip().split(":")
        image = vars[0].split("/")[-1].replace("-", "_")
        tag = vars[-1]
        value_to_add = "{}_TAG={}\n".format(image.upper(), tag)
        key = "{}_TAG".format(image.upper())
        print("Added tag {}".format(value_to_add))
        update_env.update({key: value_to_add})

for line in fileinput.input([ENV_FILE], inplace=True):
    if "=" in line:
        key = line.split("=")[0]
        if key in update_env:
            sys.stdout.write(update_env[key])
        else:
            sys.stdout.write(line)
    else:
        sys.stdout.write(line)
