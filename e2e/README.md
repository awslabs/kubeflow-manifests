
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