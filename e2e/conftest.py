
def pytest_addoption(parser):
    parser.addoption("--metadata", action="store", help="Metadata file to resume a test class from.")
    parser.addoption("--keepsuccess", action="store_true", default=False, help="Keep successfully created resources on delete.")
    parser.addoption("--region", action="store", help="Region to run the tests in. Will be overriden if metadata is provided and region is present.")