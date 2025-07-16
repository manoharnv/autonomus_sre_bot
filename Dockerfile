# Use Alpine with Python 3.10
FROM python:3.12-alpine

# Set working directory
WORKDIR /app

# Install build dependencies and runtime dependencies
RUN apk add --no-cache --virtual .build-deps gcc musl-dev python3-dev \
    && apk add --no-cache libffi-dev openssl-dev

# Copy requirements and install dependencies
COPY pyproject.toml /app/
COPY src/ /app/src/

# Install dependencies with a workaround for dependency conflicts
RUN pip install --no-cache-dir pip==24.3.1 && \
    pip install --no-cache-dir "pydantic>=2.4.2" "python-dotenv>=1.0.0" && \
    pip install --no-cache-dir crewai && \
    pip install --no-cache-dir -e . && \
    apk del .build-deps

# Copy configuration files
COPY .env /app/

# Set environment variable to indicate running in container
ENV RUNNING_IN_CONTAINER=true

# Create an entrypoint script
RUN echo '#!/bin/sh' > /app/entrypoint.sh && \
    echo 'python -m autonomous_sre_bot.main run_incident_management $@' >> /app/entrypoint.sh && \
    chmod +x /app/entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]