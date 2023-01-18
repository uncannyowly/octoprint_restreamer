# Octoprint: Restreamer Plugin
Octoprint front end to [Restreamer](https://hub.docker.com/r/datarhei/restreamer) container by datarhei.  
  
Notes:  

- This will start/stop your Restreamer container.
  - Container starts stream automatically.
- Configuration of docker container stream is separate from this plugin.  
  - User, password, and stream configs must be done inside container.
- Currently coded to look for a single stream type.
  
This code is based on work by jneilliii from their [Youtube Live plugin](https://github.com/jneilliii/OctoPrint-YouTubeLive).  

# Troubleshooting
If you get an error regarding curl-config missing and are on a Debian based OS:  

sudo apt install libcurl4-openssl-dev libssl-dev
