+++
title = "TensorBoard"
description = "Use AWS S3 as an object store to visualize events in TensorBoard"
weight = 10
+++

[TensorBoard](https://www.tensorflow.org/tensorboard/get_started) is a tool for providing the measurements and visualizations needed during the machine learning workflow. It enables tracking experiment metrics like loss and accuracy, visualizing the model graph, projecting embeddings to a lower dimensional space, and much more.

You can configure AWS S3 as a TensorBoard object store for measurements and visualizations.

## Try it out

You can use AWS S3 as an object store with TensorBoard to visualize events.

1. Choose a service account which has access to an S3 bucket with data. The following example uses `default-editor` as the service account. The TensorBoard controller creates instances using the `default` service account by default. You can also use secrets, but this example uses [IAM roles for Service Accounts](https://docs.aws.amazon.com/eks/latest/userguide/iam-roles-for-service-accounts.html).

The following command adds S3 permissions to the `default-editor` service account.

```shell
# export cluster and profile variables
export CLUSTER_NAME=<my-cluster>
export CLUSTER_REGION=<my-cluster-region>
export PROFILE_NAMESPACE=kubeflow-user-example-com
```

```shell
# add S3 permissions to service account
eksctl create iamserviceaccount --cluster=$CLUSTER_NAME --name default-editor --namespace $PROFILE_NAMESPACE --attach-policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess --region $CLUSTER_REGION --override-existing-serviceaccounts --approve
```

2. Create a PodDefault with configurations for the S3 bucket where data is located, and the service account to use.

```shell
cat <<EOF > tb_s3_poddefault.yaml
apiVersion: kubeflow.org/v1alpha1
kind: PodDefault
metadata:
  name: tensorboard-s3-config
spec:
  desc: S3 config for us-west-2 region
  selector:
    matchLabels:
      tb-s3-config: "true"
  env:
    - name: AWS_REGION
      value: us-west-2
  serviceAccountName: default-editor
EOF

kubectl apply -f tb_s3_poddefault.yaml -n $PROFILE_NAMESPACE
```

3. Head over to the TensorBoard UI and use AWS S3 as object store location. Select the Configuration you just created while creating a new TensorBoard instance.

![Create new Tensorboard](../../images/tensorboard/tensorboard-create.png)

4. Click the connect button once the TensorBoard instance is ready.
