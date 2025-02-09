# Build stage
FROM python:3.9-slim as builder

WORKDIR /app
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code and setup.py
COPY src/ ./src/
COPY main.py .

# Install the package
RUN pip install -e .

# Runtime stage
FROM python:3.9-slim

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY --from=builder /app/src ./src
COPY --from=builder /app/main.py .

CMD ["python", "main.py"]
