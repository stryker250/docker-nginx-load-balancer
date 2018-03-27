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

**APP_SSL_CERT**  
The name used for the secret mount for the SSL Certificate.

**APP_SSL_KEY**  
The name used for the secret mount for the SSL Key.

SSL Certificates and Keys are stored in secrets and mounted on the container using the ***/etc/nginx/ssl/<name>*** custom path.

Example labels:  
```
APP_NAME=testapp
APP_EXT_PORT=443
APP_INT_PORT=80
APP_HOST_NAME=test.app
APP_HTTPS=yes
APP_SSL_CERT=ssl.cert
APP_SSL_KEY=ssl.key
```

**Example usage**  
Create the secret for the SSL Certificate:  
```
docker secret create ssl-cert cert.pem
```
***This assumes the certificate file is called cert.pem, and we are calling the secret ssl-cert***

Create the secret for the SSL Key:  
```
docker secret create ssl-key cert.key
```
***This assumes the SSL key file is called cert.key, and we are calling the secret ssl-key***

Create the service:  
```
docker service create -d -p 80:80 -p 443:443 \
--mount type=bind,source=/var/run/docker.sock,destination=/var/run/docker.sock \
--secret src=ssl-cert,target="/etc/nginx/ssl/ssl.cert" \
--secret src=ssl-key,target="/etc/nginx/ssl/ssl.key" \
--network <OVERLAY_NETWORK> --replicas 1 --name load-balancer \
stryker250/docker-nginx-load-balancer
```

***Replace <OVERLAY_NETWORK> with an existing overlay network, or create one***
