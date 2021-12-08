
# README WIP

## Usage

Currently only runs tests in `ap-south-1`. Will be fixed.

Install dependencies
```
python3
kustomize
eksctl
kubectl

awscli # configure your default credentials

# install python dependencies
pip install -r requirements.txt
```

Run all
```
pytest
```

Run specific
```
pytest <test_file.py>
```

Run with output
```
pytest -s
```

Run without deleting successfully created resources. 
Usefull for rerunning failed tests.
```
pytest -s -q --keepsuccess
```

Resume from a previous run using the resources that were previous created
```
pytest -s pytest -s -q --metadata .metadata/metadata-1638939746471968000 --keepsuccess
```