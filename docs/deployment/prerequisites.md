# Prerequisites

This guide assumes that you have:

1. Installed the following tools on the client machine
    - [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) - A command line tool for interacting with AWS services.
    - [eksctl](https://eksctl.io/introduction/#installation) - A command line tool for working with EKS clusters.
    - [kubectl](https://kubernetes.io/docs/tasks/tools) - A command line tool for working with Kubernetes clusters.
    - [yq](https://mikefarah.gitbook.io/yq) - A command line tool for YAML processing. (For Linux environments, use the [wget plain binary installation](https://github.com/mikefarah/yq/#install))
    - [jq](https://stedolan.github.io/jq/download/) - A command line tool for processing JSON.
    - [kustomize version 3.2.0](https://github.com/kubernetes-sigs/kustomize/releases/tag/v3.2.0) - A command line tool to customize Kubernetes objects through a kustomization file.
      - :warning: Kubeflow is not compatible with the latest versions of of kustomize 4.x. This is due to changes in the order resources are sorted and printed. Please see [kubernetes-sigs/kustomize#3794](https://github.com/kubernetes-sigs/kustomize/issues/3794) and [kubeflow/manifests#1797](https://github.com/kubeflow/manifests/issues/1797). We know this is not ideal and are working with the upstream kustomize team to add support for the latest versions of kustomize as soon as we can.
   - [python](https://www.python.org/downloads/) - A programming language used for automated installation scripts.
   - [pip](https://pip.pypa.io/en/stable/installation/) - A package installer for python.
   
1. Creating an EKS cluster
    - If you do not have an existing cluster, run the following command to create an EKS cluster. More details about cluster creation via `eksctl` can be found [here](https://eksctl.io/usage/creating-and-managing-clusters/).
    - Various controllers in Kubeflow deployment use IAM roles for service accounts(IRSA). An OIDC provider must exist for your cluster to use IRSA.
    - Substitute values for the `CLUSTER_NAME` and `CLUSTER_REGION` in the script below
        ```
        export CLUSTER_NAME=$CLUSTER_NAME
        export CLUSTER_REGION=$CLUSTER_REGION
        ```

    - Run the following command to create an EKS Cluster
        ```
        eksctl create cluster \
        --name ${CLUSTER_NAME} \
        --version 1.20 \
        --region ${CLUSTER_REGION} \
        --nodegroup-name linux-nodes \
        --node-type m5.xlarge \
        --nodes 5 \
        --nodes-min 5 \
        --nodes-max 10 \
        --managed \
        --with-oidc
        ```
    - **Note:** If you are using an existing cluster, Create an OIDC provider and associate it with for your EKS cluster by running the following command:
        ```
        eksctl utils associate-iam-oidc-provider --cluster ${CLUSTER_NAME} \
        --region ${CLUSTER_REGION} --approve
        ```

1. Clone the `awslabs/kubeflow-manifest` repo, `kubeflow/manifests` repo and checkout the release branches.
    - Substitute the value for `KUBEFLOW_RELEASE_VERSION`(e.g. v1.4.1) and `AWS_RELEASE_VERSION`(e.g. v1.4.1-aws-b1.0.0) with the tag or branch you want to use below. Read more about [releases and versioning](../../community/releases.md#releases-and-versioning) policy if you are unsure about what these values should be.
        ```
        export KUBEFLOW_RELEASE_VERSION=<>
        export AWS_RELEASE_VERSION=<>
        git clone https://github.com/awslabs/kubeflow-manifests.git && cd kubeflow-manifests
        git checkout ${AWS_RELEASE_VERSION}
        git clone --branch ${KUBEFLOW_RELEASE_VERSION} https://github.com/kubeflow/manifests.git upstream
        ```
