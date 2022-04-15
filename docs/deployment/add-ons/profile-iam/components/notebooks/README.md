# AWS IAM for Kubeflow Profiles in Notebooks

## Configuration

Prerequisites for setting up AWS IAM for Kubeflow Profiles can be found [here](../../../profile-iam). The prerequisite steps will go through creating a profile that uses the `AwsIamForServiceAccount` plugin.

No additional configuration steps are required.

## Try It Out
1. Create a notebook server through the central dashboard.
1. Select the profile name from the top left drop down menu for the profile you created.
1. Create a notebook from [the sample](samples/verify_notebook.ipynb).
1. Run the notebook, it should be able to list the S3 buckets present in your account.