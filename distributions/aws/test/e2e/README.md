
## Usage

Install dependencies
```
python3
kustomize   # MUST BE VERSION 3.2.0
eksctl
kubectl

awscli # configure your default credentials

# install python dependencies
pip install -r requirements.txt
```

Run all
```
pytest -q --region <REGION_NAME>
```

Run specific
```
pytest <test_file.py> -k <test_name(s)> --region <REGION_NAME>
```

Run with output
```
pytest -s -q --region <REGION_NAME>
```

Run without deleting successfully created resources. 
Usefull for rerunning failed tests.
```
pytest -s -q --keepsuccess --region <REGION_NAME>
```

Resume from a previous run using the resources that were previous created
```
pytest -s pytest -s -q --metadata .metadata/metadata-1638939746471968000 --keepsuccess --region <REGION_NAME>
```

### About metadata
When using the helper method `configure_resource_fixture` a metadata file is generated with the following output:
```
# Using cluster as an example

Saved key: cluster_name value: e2e-test-cluster-507uvuyhca in metadata file /Users/rkharse/kf-e2e-tests/e2e/.metadata/metadata-1639087995874492000
```

Metadata can also be manually be output to a file by calling `Metadata#to_file` on a metadata object