import pytest
import subprocess

def kustomize_build(manifest_path):
    return subprocess.call(f"kustomize build {manifest_path}".split())

TO_ROOT = "../../"
DEPLOYMENTS_FOLDER = TO_ROOT + "docs/deployment/"

def test_vanilla():
    manifest_path = DEPLOYMENTS_FOLDER + "vanilla"
    retcode = kustomize_build(manifest_path)
    assert retcode == 0

def test_rds_s3():
    manifest_path = DEPLOYMENTS_FOLDER + "rds-s3/base"
    retcode = kustomize_build(manifest_path)
    assert retcode == 0

def test_rds():
    manifest_path = DEPLOYMENTS_FOLDER + "rds-s3/rds-only"
    retcode = kustomize_build(manifest_path)
    assert retcode == 0

def test_s3():
    manifest_path = DEPLOYMENTS_FOLDER + "rds-s3/s3-only"
    retcode = kustomize_build(manifest_path)
    assert retcode == 0

def test_cognito():
    manifest_path = DEPLOYMENTS_FOLDER + "cognito"
    retcode = kustomize_build(manifest_path)
    assert retcode == 0

def test_cognito_rds_s3():
    manifest_path = DEPLOYMENTS_FOLDER + "cognito-rds-s3"
    retcode = kustomize_build(manifest_path)
    assert retcode == 0