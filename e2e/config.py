import pytest
import time
import json
import os

from e2e.utils import safe_open

METADATA_FOLDER = './.metadata'

class Metadata:
    def __init__(self, params=None):
        if params:
            self.params = params
        else:
            self.params = {}
    
    def insert(self, key, value):
        self.params[key] = value

    def save(self, key, value):
        self.insert(key, value)
        self.to_file()
    
    def get(self, key):
        if key not in self.params:
            return None

        return self.params[key]

    def to_file(self):
        filename = 'metadata-' + str(time.time_ns())
        filepath = os.path.abspath(os.path.join(METADATA_FOLDER, filename))

        with safe_open(filepath, 'w') as file:
            json.dump(self.params, file)

        return filepath

    def from_file(filepath):
        with open(filepath) as file:
            return Metadata(json.load(file))

@pytest.fixture(scope="class")
def metadata(request):
    metadata_file = request.config.getoption("--metadata")
    if metadata_file:
        return Metadata.from_file(metadata_file)
    
    return Metadata()

def keep_successfully_created_resource(request):
    return request.config.getoption("--keepsuccess")

def configure_resource_fixture(metadata, request, resource_id, metadata_key, on_create, on_delete):
    if metadata.get(metadata_key):
        return metadata.get(metadata_key)

    successful_creation = False
    
    def delete():
        if successful_creation and keep_successfully_created_resource(request):
            return
        on_delete()
    request.addfinalizer(delete)

    on_create()
    metadata.save(metadata_key, resource_id)
    successful_creation = True

@pytest.fixture(scope="class")
def region(metadata):
    if metadata.get('region'):
        return metadata.get('region')

    # todo, remove hardcoded region
    region = "ap-south-1"
    metadata.insert('region', region)
    return region