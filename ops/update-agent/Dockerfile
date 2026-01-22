FROM python:3.11-alpine

WORKDIR /app

# git: for fetch/pull
# docker-cli + docker-cli-compose: for docker / docker compose (talking to host via /var/run/docker.sock)
RUN apk add --no-cache \
    ca-certificates \
    git \
    docker-cli \
    docker-cli-compose

COPY update_agent.py /app/update_agent.py

EXPOSE 9999

# Default: server mode. Runner mode is invoked via:
#   python3 /app/update_agent.py runner [--force]
ENTRYPOINT ["python3", "/app/update_agent.py"]
