FROM python:3.12-alpine

RUN addgroup -g 1000 appgroup && adduser -u 1000 -G appgroup -s /bin/sh -D appuser

WORKDIR /server
COPY server/ /server
RUN pip install -r requirements.txt


WORKDIR /app/tailscale-network-topology-mapper
COPY . /app/tailscale-network-topology-mapper
RUN if [ ! -f policy.hujson ]; then echo "ERROR: policy.hujson file not found" && exit 1; fi
RUN pip install -r requirements.txt
RUN chown -R appuser:appgroup /app
RUN python main.py

EXPOSE 8080

USER appuser

CMD ["python", "/server/server.py"]
