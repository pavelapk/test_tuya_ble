# Define the name of your proto file and Python package name
PROTO_FILE = ble.proto
PYTHON_PACKAGE = mygrpcpackage

# Paths to the protobuf and gRPC Python code generators
GRPC_PYTHON_PLUGIN = path\to\python.exe -m grpc_tools.protoc

# Input and output directories
PROTO_DIR = .\protos
GENERATED_DIR = .\generated

# Generate the Python gRPC server code
generate_python:
	$(GRPC_PYTHON_PLUGIN) --proto_path=$(PROTO_DIR) --python_out=$(GENERATED_DIR) --grpc_python_out=$(GENERATED_DIR) $(PROTO_DIR)\$(PROTO_FILE)

# Clean the generated files
clean:
	del /Q $(GENERATED_DIR)

# Compile the proto file and generate Python code
all: generate_python

.PHONY: all generate_python clean
