# Runs the Kommo MCP server over stdio.
# Kommo credentials (KOMMO_SUBDOMAIN, KOMMO_ACCESS_TOKEN, ...) are passed at runtime with -e;
# the server starts and lists its tools without them.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY kommo_mcp ./kommo_mcp
RUN pip install --no-cache-dir .

RUN useradd --create-home --uid 10001 mcp
USER mcp

ENTRYPOINT ["kommo-mcp"]
