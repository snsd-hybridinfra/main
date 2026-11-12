ARG NGINX_IMAGE=nginxinc/nginx-unprivileged:1.27-alpine
FROM ${NGINX_IMAGE}
ARG PORTAL_EDITION=production
COPY services/user-portal/nginx.conf /etc/nginx/conf.d/default.conf
COPY services/user-portal/index.html /usr/share/nginx/html/index.html
COPY services/user-portal/assets /usr/share/nginx/html/assets
COPY --chown=101:101 services/user-portal/eclipse /usr/share/nginx/html/eclipse
RUN case "$PORTAL_EDITION" in \
    production) rm /usr/share/nginx/html/eclipse/demo.html /usr/share/nginx/html/eclipse/local.html \
      /usr/share/nginx/html/eclipse/js/runtime-config.demo.js /usr/share/nginx/html/eclipse/js/runtime-config.local.js ;; \
    local) rm /usr/share/nginx/html/eclipse/demo.html /usr/share/nginx/html/eclipse/js/runtime-config.demo.js ;; \
    *) echo "PORTAL_EDITION must be production or local" >&2; exit 1 ;; \
    esac
USER 101:101
EXPOSE 8080
