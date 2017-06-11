# derpbox
derpbox is an http-based service which syncs files in a dropbox-like fashion.

usage: derpbox_agent.py [-h] root_path port

Derpbox Agent runs in the background and awaits REST requests to synchronize with a remote
client.  Any agent can act as a master.  Another background job needs to be run on the client to
"manage" a folder.

positional arguments:
  root_path   File path with which the agent will be bound
  port        Port to bind the agent to
