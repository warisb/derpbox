# derpbox
derpbox is an http-based service which syncs files in a dropbox-like fashion.

usage: derpbox_agent.py [-h] [--is-master] [--master-host ip or hostname]
                        [--master-port portnum]
                        rootpath port

Derpbox Agent which runs a background task for either a client or master to
sync a monitored directory with a specified master (if client) or to wait for
clients to push changes to it (if master)

positional arguments:
  rootpath              File path with which the agent will be bound
  port                  Port to bind the agent to

optional arguments:
  -h, --help            show this help message and exit
  --is-master           Defined if this is the master
  --master-host ip or hostname
                        Host of the master to periodically sync against
  --master-port portnum
                        Port of the master to periodically sync against
