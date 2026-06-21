FROM ghcr.io/actions/actions-runner:2.335.1

USER root

ARG DOCKER_COMPOSE_VERSION=v5.1.4

COPY entrypoint.sh /usr/local/bin/homelab-runner-entrypoint
RUN mkdir -p /usr/local/lib/docker/cli-plugins \
    && curl -fsSL "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-linux-x86_64" \
      -o /usr/local/lib/docker/cli-plugins/docker-compose \
    && chmod +x /usr/local/lib/docker/cli-plugins/docker-compose \
    && chmod +x /usr/local/bin/homelab-runner-entrypoint

WORKDIR /home/runner
ENTRYPOINT ["/usr/local/bin/homelab-runner-entrypoint"]
