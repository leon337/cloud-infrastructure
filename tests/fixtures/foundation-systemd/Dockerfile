FROM ubuntu@sha256:561618e2c15bf2397621dd04f96926663a3b5616c189cf7e38db7e82f5c538ea

ENV DEBIAN_FRONTEND=noninteractive

COPY requirements-dev.lock /tmp/requirements-dev.lock

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        ca-certificates \
        lsof \
        passwd \
        procps \
        python3 \
        python3-venv \
        sudo \
        systemd \
        systemd-sysv \
        util-linux \
    && python3 -m venv /opt/foundation-test-venv \
    && /opt/foundation-test-venv/bin/pip install \
        --disable-pip-version-check \
        --no-cache-dir \
        --requirement /tmp/requirements-dev.lock \
    && apt-get clean \
    && rm -f /tmp/requirements-dev.lock \
    && rm -rf /var/lib/apt/lists/* \
    && systemctl mask \
        systemd-networkd-wait-online.service \
        systemd-resolved.service

COPY repository/ /workspace/cloud-infrastructure/

STOPSIGNAL SIGRTMIN+3
CMD ["/sbin/init"]
