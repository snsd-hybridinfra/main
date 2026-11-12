ARG CRS_IMAGE=owasp/modsecurity-crs:4.25.0-nginx-lts
FROM ${CRS_IMAGE}

ENV MODSEC_RULE_ENGINE=on \
    MODSEC_AUDIT_ENGINE=RelevantOnly \
    MODSEC_AUDIT_LOG=/dev/stdout \
    MODSEC_AUDIT_LOG_FORMAT=JSON \
    BLOCKING_PARANOIA=1 \
    DETECTION_PARANOIA=1 \
    ANOMALY_INBOUND=5 \
    ANOMALY_OUTBOUND=4

COPY --chown=nginx:nginx security/nginx/nginx.conf /opt/edge-config/nginx.conf
COPY --chown=nginx:nginx security/nginx/edge.conf.template /opt/edge-config/edge.conf.template
COPY --chown=nginx:nginx security/nginx/docker-entrypoint.sh /opt/edge-config/docker-entrypoint.sh
COPY --chown=nginx:nginx security/modsecurity/REQUEST-900-EXCLUSION-RULES-BEFORE-CRS.conf /opt/owasp-crs/rules/REQUEST-900-EXCLUSION-RULES-BEFORE-CRS.conf
COPY --chown=nginx:nginx security/modsecurity/RESPONSE-999-EXCLUSION-RULES-AFTER-CRS.conf /opt/owasp-crs/rules/RESPONSE-999-EXCLUSION-RULES-AFTER-CRS.conf
# Freeze the official ModSecurity/CRS templates during the image build. Runtime
# only renders the environment-specific vhosts into /tmp, so the pod can keep a
# read-only root filesystem.
RUN /docker-entrypoint.sh /bin/true

USER nginx
EXPOSE 8443
ENTRYPOINT ["/bin/sh", "/opt/edge-config/docker-entrypoint.sh"]
