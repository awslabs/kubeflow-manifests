
def pytest_addoption(parser):
    parser.addoption("--metadata", action="store", help="metadata file to resume tests from")
    parser.addoption("--keepsuccess", action="store_true", default=False, help="Keep successfully created resources on delete")