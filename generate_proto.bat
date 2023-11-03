@echo off

:: Define the paths and variables
set PROTO_FILE=ble.proto
set PYTHON_PACKAGE=mygrpcpackage
set GRPC_PYTHON_PLUGIN="venv\Scripts\python.exe -m grpc_tools.protoc"
set PROTO_DIR=.\protos
set GENERATED_DIR=.\generated

:: Create the output directory if it doesn't exist
if not exist %GENERATED_DIR% mkdir %GENERATED_DIR%

call .\venv\Scripts\activate

:: Generate the Python gRPC server code
python.exe -m grpc_tools.protoc --proto_path=%PROTO_DIR% --python_out=%GENERATED_DIR% --pyi_out=%GENERATED_DIR% --grpc_python_out=%GENERATED_DIR% %PROTO_DIR%\%PROTO_FILE%

deactivate

:: Pause the script to see the results
pause
