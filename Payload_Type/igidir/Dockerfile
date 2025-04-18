FROM python:3.10-slim as builder

WORKDIR /Mythic/

# Install dependencies
RUN apt-get update && \
    apt-get install -y gcc g++ make procps && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy over required files
COPY ["requirements.txt", "/Mythic/"]
COPY rabbitmq_config.json /Mythic/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt


FROM python:3.10-slim

WORKDIR /Mythic/

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the agent code
COPY . /Mythic/

# Set the entrypoint
ENTRYPOINT ["python", "main.py"]