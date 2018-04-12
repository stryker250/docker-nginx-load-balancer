#!/usr/bin/env python

from __future__ import print_function
import docker
import os
import signal
from sys import exit, stderr
import jinja2
import subprocess
import time

DOCKER_HOST = os.environ.get('DOCKER_HOST', 'unix:///var/run/docker.sock')
client = docker.DockerClient(base_url=DOCKER_HOST)

upstreams = {}
servers = {}
added_containers = []

template_loader = jinja2.FileSystemLoader(searchpath='./templates')
template_evironment = jinja2.Environment(loader=template_loader)


def update_config():
    try:
        template = template_evironment.get_template('loadbalancer.conf')
        with open('/etc/nginx/conf.d/loadbalancer.conf', 'w') as f:
            conf = template.render(upstreams=upstreams, servers=servers)
            f.write(conf)
        subprocess.call(["nginx", "-s", "reload"])
    except jinja2.TemplateError, e:
        print('Unable to update NGINX configuration: %s' % e, file=stderr)
    except Exception, e:
        print('Unable to update NGINX configuration: %s' %e, file=stderr)

def add_containers():
    containers = client.containers.list(all=True, filters={'label':'APP_NAME'})
    for container in containers:
        attributes = container.attrs['Config']['Labels']
        id = container.id
        app_ext_port = '80'
        app_int_port = '80'
        app_hostname = ''
        app_https = False
        app_ssl_cert = 'ssl.cert'
        app_ssl_key = 'ssl.key'
        # hostname = container.attrs['Config']['Hostname']
        hostname = container.name
        if container.status == 'running':
            changed = False
            app_name = attributes['APP_NAME']
            if 'APP_EXT_PORT' in attributes:
                app_ext_port = attributes['APP_EXT_PORT']
            if 'APP_INT_PORT' in attributes:
                app_int_port = attributes['APP_INT_PORT']
            if 'APP_HOST_NAME' in attributes:
                app_hostname = attributes['APP_HOST_NAME']
            if 'APP_HTTPS' in attributes and \
                attributes['APP_HTTPS'].lower() == 'yes':
                app_https = True
            if 'APP_SSL_CERT' in attributes:
                app_ssl_cert = attributes['APP_SSL_CERT']
            if 'APP_SSL_KEY' in attributes:
                app_ssl_key = attributes['APP_SSL_KEY']

            upstream_address = hostname + ':' + app_int_port

            if app_name in upstreams:
                if upstream_address not in upstreams[app_name]['addresses']:
                    upstreams[app_name]['addresses'].append(upstream_address)
                    changed = True
                    added_containers.append({
                        'id': id,
                        'app_name': app_name,
                        'upstream_address': upstream_address,
                        'app_hostname': app_hostname
                    })
            else:
                upstreams[app_name] = {
                    'addresses': [upstream_address]
                }
                changed = True
                added_containers.append({
                    'id': id,
                    'app_name': app_name,
                    'upstream_address': upstream_address,
                    'app_hostname': app_hostname
                })

            if app_hostname not in servers:
                servers[app_hostname] = {
                    'https': app_https,
                    'port': app_ext_port,
                    'upstream': app_name,
                    'ssl_cert': app_ssl_cert,
                    'ssl_key': app_ssl_key
                }
            if changed:
                print('Updating NGINX Configuration', file=stderr)
                update_config()

def remove_containers():
    for _container in added_containers:
        _id = _container['id']
        app_name = _container['app_name']
        upstream_address = _container['upstream_address']
        app_hostname = _container['app_hostname']
        remove = False
        changed = False
        try:
            container = client.containers.get(_id)
            if container.status != 'running':
                remove = True
        except docker.errors.NotFound:
            remove = True

        if remove:
            if app_name in upstreams:
                if upstream_address in upstreams[app_name]['addresses']:
                    upstreams[app_name]['addresses'].remove(upstream_address)
                    changed = True
                if len(upstreams[app_name]['addresses']) == 0:
                    del upstreams[app_name]
                    changed = True
                    if app_hostname in servers:
                        del servers[app_hostname]
                        changed = True

                if changed:
                    print('Updating NGINX Configuration', file=stderr)
                    update_config()
                    added_containers.remove(_container)

def docker_checker():
    while True:
        add_containers()
        remove_containers()
        time.sleep(5)

def graceful_shutdown(signal, frame):
    print('shutting down...', file=stderr)
    exit(0)

def main():
    signal.signal(signal.SIGTERM, graceful_shutdown)
    docker_checker()

if __name__ == '__main__':
    main()
