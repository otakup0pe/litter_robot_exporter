# Use alpine image
FROM alpine:latest

# Set the working directory in the container to /app
WORKDIR /app

# Add the current directory contents into the container at /app
ADD . /app

RUN apk add --no-cache python3 py3-pip rust libffi-dev python3-dev cargo openssl-dev tzdata

# Install any needed packages specified in requirements.txt
RUN /usr/bin/python3 -m venv /venv && \
    /venv/bin/python3 -m pip install -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Run exporter.py when the container launches
CMD ["/venv/bin/python", "/app/exporter.py"]