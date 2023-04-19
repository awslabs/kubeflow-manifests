+++
title = "Configure Culling for Notebooks"
description = "Automatically stop your notebooks based on idleness"
weight = 80
+++

 The culling feature allows you to stop a Notebook Server based on its **Last Activity**. The Notebook Controller updates the respective `notebooks.kubeflow.org/last-activity` annotation of each Notebook resource according to the execution state of the kernels. When this feature is enabled, the notebook instances will be "culled" (scaled to zero) if none of the kernels are performing computations for a specified period of time (`CULL_IDLE_TIME`). More information about this feature can be found in the [Jupyter notebook idleness proposal](https://github.com/kubeflow/kubeflow/blob/master/components/proposals/20220121-jupyter-notebook-idleness.md).

1. Export the following values values to configure the [culling policy parameters](https://github.com/kubeflow/kubeflow/blob/master/components/proposals/20220121-jupyter-notebook-idleness.md#api-changes):
    ```bash
    # whether to enable culling feature (true/false). ENABLE_CULLING must be set to “true” for this feature to take work
    export ENABLE_CULLING="true"
    # specified idleness time (minutes) that notebook instance to be culled since last activity
    export CULL_IDLE_TIMEOUT="30"
    # controller will update each notebook's LAST_ACTIVITY_ANNOTATION every IDLENESS_CHECK_PERIOD (minutes)
    export IDLENESS_CHECK_PERIOD="5"
    ```

1. The following commands will inject those values in a configuration file for setting up Notebook culling:
    Select the package manager of your choice.
    - For Kustomize and Helm:
    {{< tabpane persistLang=false >}}
    {{< tab header="Kustomize" lang="sh" >}}
printf '
ENABLE_CULLING='$ENABLE_CULLING'
CULL_IDLE_TIME='$CULL_IDLE_TIMEOUT'
IDLENESS_CHECK_PERIOD='$IDLENESS_CHECK_PERIOD'
' > awsconfigs/apps/notebook-controller/params.env
    {{< /tab >}}
    {{< tab header="Helm" lang="sh" >}}
yq e '.cullingPolicy.enableCulling = env(ENABLE_CULLING)' -i charts/apps/notebook-controller/values.yaml
yq e '.cullingPolicy.cullIdleTime = env(CULL_IDLE_TIMEOUT)' -i charts/apps/notebook-controller/values.yaml
yq e '.cullingPolicy.idlenessCheckPeriod = env(IDLENESS_CHECK_PERIOD)' -i charts/apps/notebook-controller/values.yaml
    {{< /tab >}}
    {{< /tabpane >}}
    
    - For Terraform, append the notebook culling parameters in the `sample.auto.tfvars` file with chosen deployment option: [Vanilla]({{< ref "/docs/deployment/vanilla/guide-terraform.md#" >}}), [Cognito]({{< ref "/docs/deployment/cognito/guide-terraform.md#" >}}), [RDS-S3]({{< ref "/docs/deployment/rds-s3/guide-terraform.md#" >}}), and [Cognito-RDS-S3]({{< ref "/docs/deployment/cognito-rds-s3/guide-terraform.md#" >}}).

        ```sh
        cat <<EOT >> sample.auto.tfvars
        notebook_enable_culling="${ENABLE_CULLING}" 
        notebook_cull_idle_time="${CULL_IDLE_TIMEOUT}"
        notebook_idleness_check_period="${IDLENESS_CHECK_PERIOD}"
        EOT
        ```

1. Continue deploying Kubeflow based on your [Deployment Option]({{< ref "/docs/deployment/_index.md#" >}}).
