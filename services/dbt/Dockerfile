FROM python:3.11-slim

# Install system deps (git is REQUIRED by dbt)
RUN apt-get update \
    && apt-get install -y git \
    && rm -rf /var/lib/apt/lists/*
    
WORKDIR /dbt

RUN pip install --no-cache-dir \
    dbt-core==1.11.2 \
    dbt-postgres==1.10.0

COPY . /dbt

ENTRYPOINT ["dbt"]
