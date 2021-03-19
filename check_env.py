import sys


def get_keys_from_file(file_name):
    all_keys = {}
    try:
        with open(file_name, "r") as stream:
            lines = stream.readlines()
            for line in lines:
                split_line = line.split("=")
                if len(split_line) == 2:
                    if split_line[1] == "\n":
                        all_keys[split_line[0]] = False
                    else:
                        all_keys[split_line[0]] = True
    except FileNotFoundError:
        print(f"Could not find file {file_name}. Aborting.")
        sys.exit(1)
    return all_keys


def get_keys_from_config_file(file_name):
    all_keys = {}
    try:
        with open(file_name, "r") as stream:
            lines = stream.readlines()
            for line in lines:
                split_line = line.split(":")
                if len(split_line) >= 2:
                    if split_line[1] == "\n":
                        all_keys[split_line[0].strip()] = False
                    else:
                        all_keys[split_line[0].strip()] = True
    except FileNotFoundError:
        print(f"Could not find file {file_name}. Aborting.")
        sys.exit(1)
    return all_keys


if __name__ == "__main__":
    if sys.argv[3] == "env":
        env_in = get_keys_from_file(sys.argv[1])
        env_to_check = get_keys_from_file(sys.argv[2])
        for k, v in env_in.items():
            if k in env_to_check:
                if env_to_check[k]:
                    continue
                else:
                    print(f"{k} is not set in your env file.")
            else:
                print(f"{k} is missing as a key in your env file.")
    elif sys.argv[3] == "config":
        config_in = get_keys_from_config_file(sys.argv[1])
        config_to_check = get_keys_from_config_file(sys.argv[2])
        for k, v in config_in.items():
            if k in config_to_check:
                if config_to_check[k]:
                    continue
                else:
                    if not v:
                        print(
                            f"{k} is not set in your config file. Could also be a yml key."
                        )
                    else:
                        print(f"{k} is not set in your config file.")
            else:
                print(f"{k} is missing as a key in your config file.")
    else:
        print("No information which files to check. Aborting.")
        sys.exit(1)
