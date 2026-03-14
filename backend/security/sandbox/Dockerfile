# A basic Python environment for running sandboxed agent scripts
FROM python:3.11-slim

# Create a non-root user with UID 1000
RUN useradd -m -u 1000 sandboxuser

WORKDIR /sandbox

# Copy any necessary sandbox scripts or basic utilities
# For now, it's just a clean environment
# If requirements change later, they can be added here
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt || true

USER sandboxuser

# Keep alive or default command
CMD ["python", "-c", "import time; time.sleep(3600)"]
