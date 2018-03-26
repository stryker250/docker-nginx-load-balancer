#!/usr/bin/env python

from __future__ import print_function
import docker
import os
import signal
from sys import exit, stderr
import jinja2
import subprocess

DOCKER_HOST = os.environ.get('DOCKER_HOST', 'unix:///var/run/docker.sock')

upstreams = {}
servers = {}

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


def docker_checker():
    client = docker.DockerClient(base_url=DOCKER_HOST)
    filters = {
        'type': 'container'
    }
    for event in client.events(decode=True, filters=filters):
        attributes = event['Actor']['Attributes']
        app_ext_port = '80'
        app_int_port = '80'
        app_hostname = ''
        app_https = False
        if event['status'] == 'start':
            if 'APP_NAME' in attributes:
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

                hostname = attributes['name']

                upstream_address = hostname + ':' + app_int_port

                if app_name in upstreams:
                    if upstream_address not in upstreams[app_name]['addresses']:
                        upstreams[app_name]['addresses'].append(upstream_address)
                else:
                    upstreams[app_name] = {
                        'addresses': [upstream_address]
                    }

                if app_hostname not in servers:
                    servers[app_hostname] = {
                        'https': app_https,
                        'port': app_ext_port,
                        'upstream': app_name
                    }

                print('Updating NGINX Configuration', file=stderr)
                update_config()
        elif event['status'] == 'stop' or event['status'] == 'kill':
            if 'APP_NAME' in attributes:
                app_name = attributes['APP_NAME']
                if 'APP_EXT_PORT' in attributes:
                    app_ext_port = attributes['APP_EXT_PORT']
                if 'APP_INT_PORT' in attributes:
                    app_int_port = attributes['APP_INT_PORT']
                if 'APP_HOST_NAME' in attributes:
                    app_hostname = attributes['APP_HOST_NAME']
                hostname = attributes['name']

                upstream_address = hostname + ':' + app_int_port

                if app_name in upstreams:
                    if upstream_address in upstreams[app_name]['addresses']:
                        upstreams[app_name]['addresses'].remove(upstream_address)
                    if len(upstreams[app_name]['addresses']) == 0:
                        del upstreams[app_name]
                        if app_hostname in servers:
                            del servers[app_hostname]

                print('Updating NGINX Configuration', file=stderr)
                update_config()


def graceful_shutdown(signal, frame):
    print('shutting down...', file=stderr)
    exit(0)

def main():
    signal.signal(signal.SIGTERM, graceful_shutdown)
    docker_checker()

if __name__ == '__main__':
    main()
