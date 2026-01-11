FROM python:3.12-alpine

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN addgroup -g 1000 appgroup && adduser -u 1000 -G appgroup -s /bin/sh -D appuser

# Install server dependencies
WORKDIR /server
COPY server/ /server
RUN uv pip install --system -r requirements.txt

# Install main application dependencies
WORKDIR /app/tailscale-network-topology-mapper
COPY pyproject.toml requirements.txt /app/tailscale-network-topology-mapper/
RUN uv pip install --system -r requirements.txt

# Copy application code
COPY . /app/tailscale-network-topology-mapper
RUN if [ ! -f policy.hujson ]; then echo "ERROR: policy.hujson file not found" && exit 1; fi
RUN chown -R appuser:appgroup /app
RUN python main.py

EXPOSE 8080

USER appuser

CMD ["python", "/server/server.py"]
