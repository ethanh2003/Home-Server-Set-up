FROM ghcr.io/actions/actions-runner:2.335.1

USER root

COPY entrypoint.sh /usr/local/bin/homelab-runner-entrypoint
RUN chmod +x /usr/local/bin/homelab-runner-entrypoint

WORKDIR /home/runner
ENTRYPOINT ["/usr/local/bin/homelab-runner-entrypoint"]
