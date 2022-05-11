#!/bin/bash

# All the inputs to this script as environment variables 
# REPO_PATH : Local root path of the kubeflow-manifest github repo 

# Script configuration
set -euo pipefail

function onError {
  echo "Run test FAILED. Exiting."
}
trap onError ERR

export E2E_TEST_DIR=${REPO_PATH}/tests/e2e

cd $E2E_TEST_DIR
pytest tests/test_sanity_portforward.py -s -q  --region $AWS_DEFAULT_REGION


