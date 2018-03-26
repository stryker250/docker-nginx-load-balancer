# Docker NGINX Load Balancer

This image will create the configuration for the load balancer by listening for Docker container events.
If the container being started contains the labels for the load balancer, the configuration will be updated accordingly.

The path / URL to the Docker environment can be set as an environment variable, or the default socket file will be used.

```
DOCKER_HOST = unix:///var/run/docker.sock
```

The following labels will be checked for load balancing:

**APP_NAME**  
The name of the application, this is used to group the servers together and is used as the upstream name.

**APP_EXT_PORT**  
The external port the load balancer should be listening on.

**APP_INT_PORT**  
The internal port the load balancer should be forwarding to.

**APP_HOST_NAME**  
The hostname the load balancer should be checking.

**APP_HTTPS**  
Whether or not SSL should be enabled.

SSL Certificates need to be manually copied to the container at this time.
SSL Certificates should be copied to:  
- Certificate -> /etc/nginx/ssl/<APP_HOST_NAME>/ssl.cert
- Key -> /etc/nginx/ssl/<APP_HOST_NAME>/ssl.key

Example lables:  
```
APP_NAME=testapp
APP_EXT_PORT=443
APP_INT_PORT=80
APP_HOST_NAME=test.app
APP_HTTPS=yes
```
