"""
Add additional pytest supported test configurations.

https://docs.pytest.org/en/6.2.x/example/simple.html
"""

import pytest

def pytest_addoption(parser):
    parser.addoption("--metadata", action="store", help="Metadata file to resume a test class from.")
    parser.addoption("--keepsuccess", action="store_true", default=False, help="Keep successfully created resources on delete.")
    parser.addoption("--region", action="store", help="Region to run the tests in. Will be overriden if metadata is provided and region is present.")

def keep_successfully_created_resource(request):
    return request.config.getoption("--keepsuccess")

def load_metadata_file(request):
    return request.config.getoption("--metadata")

@pytest.fixture(scope="class")
def region(metadata, request):
    """
    Test region.
    """

    if metadata.get('region'):
        return metadata.get('region')

    region = request.config.getoption("--region")
    metadata.insert('region', region)
    return region


