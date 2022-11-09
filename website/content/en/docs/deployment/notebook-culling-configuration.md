+++
title = "Configure Culling for Notebooks"
description = "Configure Notebook Culling Feature"
weight = 70
+++

### (Optional) 
You can expose the timestamp of the last-activity of a Notebook instance and enable culling mechanism with that information. The notebook instance will be "culled" if it has been idled for the specified period of time. The design doc of the feature can be found in [here](https://github.com/kubeflow/kubeflow/blob/master/components/proposals/20220121-jupyter-notebook-idleness.md)

1. Export these values for [culling parameters](https://github.com/kubeflow/kubeflow/blob/master/components/proposals/20220121-jupyter-notebook-idleness.md#api-changes):
    ```bash
    export ENABLE_CULLING="whether to enable culling feature (true/false)"
    export CULL_IDLE_TIMEOUT="specified idleness time (minutes) that notebook instance to be culled since last activity"
    export IDLENESS_CHECK_PERIOD="controller will update each notebook's LAST_ACTIVITY_ANNOTATION every IDLENESS_CHECK_PERIOD (minutes)"
    ```

1. The following commands will inject those values in a configuration file for setting up Notebook culling:
    Select the package manager of your choice.
    {{< tabpane persistLang=false >}}
    {{< tab header="Kustomize" lang="toml" >}}
printf '
enableCulling='$ENABLE_CULLING'
cullIdleTime='$CULL_IDLE_TIMEOUT'
idlenessCheckPeriod='$IDLENESS_CHECK_PERIOD'
' > awsconfigs/apps/notebook-controller/params.env
    {{< /tab >}}
    {{< tab header="Helm" lang="yaml" >}}
yq e '.cullingPolicy.enableCulling = env(ENABLE_CULLING)' -i charts/apps/notebook-controller/values.yaml
yq e '.cullingPolicy.cullIdleTime = env(CULL_IDLE_TIMEOUT)' -i charts/apps/notebook-controller/values.yaml
yq e '.cullingPolicy.idlenessCheckPeriod = env(IDLENESS_CHECK_PERIOD)' -i charts/apps/notebook-controller/values.yaml
    {{< /tab >}}
    {{< /tabpane >}}
1. For [Terraform option]({{< ref "/docs/deployment/vanilla/guide-terraform.md#" >}}) , modify the notebook-controller chart values per the Helm option in previous step, then deploy with Terraform with your deployment option.

1. Deploy Kubeflow based on your [Deployment Option]({{< ref "/docs/deployment/_index.md#" >}})
