FROM public.ecr.aws/lambda/python:3.12

# Install Node.js (Required for MCP npx commands) using dnf (Amazon Linux 2023)
RUN curl -fsSL https://rpm.nodesource.com/setup_20.x | bash - \
    && dnf install -y nodejs \
    && dnf clean all

# Copy requirements and install them
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

# Copy all function code and services into the container
COPY . ${LAMBDA_TASK_ROOT}/

# Set the CMD to your handler
CMD [ "lambda_function.lambda_handler" ]