# derpbox
derpbox is an http-based service which syncs files in a dropbox-like fashion.  
Includes an agent (for deployment on master servers), and client (for syncing with the master)

Agent:

usage: derpbox_agent.py [-h] root_path

Derpbox Agent which provides necessary services for Derpbox Clients such as
file listor file downloads

positional arguments:
  root_path   File path with which the agent will be bound
  
Client:

usage: derpbox_client.py [-h] sync_path agent_hostname

Derpbox Client which communicates with the agent to synchronize local files
with the agent

positional arguments:
  sync_path       File path which client will synchronize
  agent_hostname  The hostname or IP of the agent
