# Start from the alpine image
FROM alpine:latest

# Install Thrift and the Python development libraries
RUN apk add --no-cache thrift-dev py3-dev

# Copy the Thrift file into the Docker container
COPY your_thrift_file.thrift /

# Generate the Python code from the Thrift file
RUN thrift -out /output -gen py your_thrift_file.thrift
