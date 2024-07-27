# Use an ARM-based base image for Python 3.11
#FROM arm32v7/python:3.11-buster
FROM python:3.11-buster

RUN pip install --upgrade pip setuptools
# Install poetry
RUN pip install poetry

# Set the working directory
WORKDIR /app

# Copy source code and project files
COPY src/ /app/src/
COPY src/templates /app/src/templates
COPY pyproject.toml .

# Create a directory for data
RUN mkdir /data
RUN mkdir /logs

# Install dependencies
RUN poetry install --no-dev

# Set the entrypoint to use Gunicorn
ENTRYPOINT ["poetry", "run", "gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "src.main:app"]
