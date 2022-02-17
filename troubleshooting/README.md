# Welcome to the client troubleshooting page
Here we list errors, problems, troubles and their (possible) solutions.

##### Common solutions to some problems
- Ran `make thrift_py` after making changes to portal_client.thrift?
- Ran `make dev` or `docker-compose up -f docker-compose.dev.yml up --build` after making changes to the py files? The docker container needs to be build anew when making changes to the .py files.
- Ran `docker-compose up -f docker-compose.dev.yml up` in local dev environment instead of `docker-compose up`? `docker-compose up` uses the docker-compose.yml for production environment.

##### Ran make thrift_py, now the client does not start anymore because of `ImportError: attempted relative import with no known parent package`?
In VirtualMachineService.py change `.ttypes import *` to `from ttypes import *`.
In constants.py change `from .ttypes import *` to `from ttypes import *`.

##### FORC does not load at startup?
Look at the startup messages in your terminal, FORC might be missing some configuration. Do you have:
- The FORC URL set in config/config.yml? Like:
```
forc:
  forc_url: https://proxy-dev.bi.denbi.de:5000/
  ...
```
- Allowed templates and their versions set in config/config.yml? Like:
```
forc:
  ...
  forc_allowed:
    theiaide:
      - v01
    rstudio:
      - v02
      - v01
```
- Do you have FORC_API_KEY set in your .env? If there is no .env in your folder and only an .env.in, create an .env file and set the FORC_API_KEY which you have set in FORC.
