FROM node:24-bookworm-slim@sha256:01d566e8d94d8c619591d78652babfccd3c6992a3dffa9ed5ab39e11cf6c70e9
RUN apt-get update && apt-get install -y --no-install-recommends bash ca-certificates curl git ripgrep python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/*
RUN npm install -g --ignore-scripts @earendil-works/pi-coding-agent@1.5.0
RUN mkdir -p /workspace /run/gateway /run/egress /home/node/.pi/agent \
    && chown -R node:node /workspace /run/gateway /run/egress /home/node
COPY config/ /opt/pi-config/
COPY gateway.py relay.cjs start.sh /opt/sandbox/
USER 1000:1000
WORKDIR /workspace
ENTRYPOINT ["/bin/bash", "/opt/sandbox/start.sh"]
