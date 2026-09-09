"""
Application configuration, fetched from AWS at startup.

Non-sensitive values come from SSM Parameter Store under /capstone-bin/.
Credentials come from Secrets Manager.

Credentials are resolved via the EC2 instance role, so nothing in this
file or the environment holds an AWS key.
"""

import json
from urllib.parse import quote_plus

import boto3

REGION = "us-east-1"
PARAM_PREFIX = "/capstone-bin"

_ssm = boto3.client("ssm", region_name=REGION)
_secrets = boto3.client("secretsmanager", region_name=REGION)


def _load_parameters(prefix):
    """Return {'postgres/host': '...', 'app/bin-ttl-hours': '48', ...}."""
    params = {}
    paginator = _ssm.get_paginator("get_parameters_by_path")
    for page in paginator.paginate(Path=prefix, Recursive=True):
        for p in page["Parameters"]:
            params[p["Name"][len(prefix) + 1:]] = p["Value"]
    return params


def _load_secret(name):
    response = _secrets.get_secret_value(SecretId=name)
    return json.loads(response["SecretString"])


def _require(params, key):
    try:
        return params[key]
    except KeyError:
        raise RuntimeError(
            f"Missing SSM parameter {PARAM_PREFIX}/{key}"
        ) from None


_params = _load_parameters(PARAM_PREFIX)
_pg = _load_secret("capstone-bin/postgres")
_mongo = _load_secret("capstone-bin/mongo")

DATABASE_URL = (
    f"postgresql://{quote_plus(_pg['username'])}:{quote_plus(_pg['password'])}"
    f"@{_require(_params, 'postgres/host')}:{_require(_params, 'postgres/port')}"
    f"/{_require(_params, 'postgres/dbname')}"
)

MONGO_URL = (
    f"mongodb://{quote_plus(_mongo['username'])}:{quote_plus(_mongo['password'])}"
    f"@{_require(_params, 'mongo/host')}:{_require(_params, 'mongo/port')}"
    f"/{_require(_params, 'mongo/dbname')}"
)

FRONTEND_ORIGINS = _require(_params, "app/frontend-origins")
SWEEP_INTERVAL_SECONDS = float(_require(_params, "app/sweep-interval-seconds"))
BIN_TTL_HOURS = float(_require(_params, "app/bin-ttl-hours"))
REQUEST_TTL_HOURS = float(_require(_params, "app/request-ttl-hours"))
MAX_REQUESTS_PER_BIN = int(_require(_params, "app/max-requests-per-bin"))