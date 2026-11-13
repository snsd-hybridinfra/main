#!/bin/sh
set -eu

required_vars='USER_HOST ADMIN_HOST IDENTITY_HOST USER_PORTAL_UPSTREAM ADMIN_PORTAL_UPSTREAM REQUEST_API_UPSTREAM APPROVAL_API_UPSTREAM GRANT_API_UPSTREAM IDENTITY_UPSTREAM IDENTITY_TLS_SERVER_NAME'
for name in ${required_vars}; do
    eval "value=\${${name}:-}"
    if [ -z "${value}" ]; then
        echo "required edge configuration is missing: ${name}" >&2
        exit 78
    fi
done

umask 077
mkdir -p /tmp/nginx/client /tmp/nginx/proxy /tmp/nginx/fastcgi /tmp/nginx/uwsgi /tmp/nginx/scgi
mkdir -p /tmp/modsecurity/data /tmp/modsecurity/tmp /tmp/modsecurity/upload

envsubst '${USER_HOST} ${ADMIN_HOST} ${IDENTITY_HOST} ${USER_PORTAL_UPSTREAM} ${ADMIN_PORTAL_UPSTREAM} ${REQUEST_API_UPSTREAM} ${APPROVAL_API_UPSTREAM} ${GRANT_API_UPSTREAM} ${IDENTITY_UPSTREAM} ${IDENTITY_TLS_SERVER_NAME}' \
    < /opt/edge-config/edge.conf.template \
    > /tmp/edge.conf

nginx -t -c /opt/edge-config/nginx.conf
exec nginx -c /opt/edge-config/nginx.conf -g 'daemon off;'
