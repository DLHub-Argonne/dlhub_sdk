"""Key configuration details"""

DLHUB_URL = "https://dlhub.org/"
DLHUB_SERVICE_ADDRESS = "https://api.dlhub.org/api/v1"
CLIENT_ID = 'f47a891c-cfd0-443c-8db8-c72fb82fe3f7'
SEARCH_INDEX = "dlhub"

# Production lambda at https://c3joreppfz4qsvxvdh5n3ehlme0bfimm.lambda-url.us-east-1.on.aws/
# Dev lambda at "https://7v5g6s33utz4l7jx6dkxuh77mu0cqdhb.lambda-url.us-east-2.on.aws/"
GLOBUS_SEARCH_WRITER_LAMBDA = "https://c3joreppfz4qsvxvdh5n3ehlme0bfimm.lambda-url.us-east-1.on.aws/"

# Scope for dev lambda: 'https://auth.globus.org/scopes/44420d77-7931-4d0e-9d2b-173aca040c0e/action_all'
# Scope for prod lambda: 'https://auth.globus.org/scopes/d31d4f5d-be37-4adc-a761-2f716b7af105/action_all'

GLOBUS_SEARCH_LAMBDA_SCOPE = 'https://auth.globus.org/scopes/d31d4f5d-be37-4adc-a761-2f716b7af105/action_all'
