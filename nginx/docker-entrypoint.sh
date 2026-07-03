#!/bin/sh

set -e

htpasswd -bc /etc/nginx/.htpasswd \
    "$NGINX_BASIC_AUTH_USER" \
    "$NGINX_BASIC_AUTH_PASSWORD"

exec nginx -g "daemon off;"
