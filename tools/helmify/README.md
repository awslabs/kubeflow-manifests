# Helmify Tool (AWS Kubeflow Distro Specific)

## Overview

The Helmify tool creates helm charts based on kustomized output. The tool consumes dictionary defined in `tools/helmify/src/config.yaml` to generates helm charts based on kustomization outputs. To run the tool, simply run `PYTHONPATH=. python tools/helmify/src/kustomize_to_helm_automation.py` in the root directory. You can also comment out components defined in `Components` inside the `kustomize_to_helm_automation.py` script to helmify only the components you want.

## Getting Started
First, make sure you have [kubeflow upstream repo](https://awslabs.github.io/kubeflow-manifests/docs/deployment/prerequisites/#clone-repository) cloned.  


Step 1. Define kubeflow component config dictionary(tools/helmify/src/config.yaml):
EXAMPLE without deployment_option subfolder in chart:
```
dex:
  kustomization_paths:
    - upstream/common/dex/overlays/istio
  output_helm_chart_path: charts/common/dex
  version: 0.1.0
  app_version: v2.24.0
```

EXAMPLE with deployment_option subfolder in chart:
```
kubeflow-pipelines:
  deployment_options:
    vanilla:
      kustomization_paths:
        - awsconfigs/apps/pipeline/base
      output_helm_chart_path: charts/apps/kubeflow-pipelines/vanilla
      version: 0.1.1
      app_version: 2.0.0-alpha.5
    rds-s3:
      kustomization_paths:
        - awsconfigs/apps/pipeline
      output_helm_chart_path: charts/apps/kubeflow-pipelines/rds-s3
      version: 0.1.1
      app_version: 2.0.0-alpha.5
    rds-only:
      kustomization_paths:
        - awsconfigs/apps/pipeline/rds
      output_helm_chart_path: charts/apps/kubeflow-pipelines/rds-only
      version: 0.1.1
      app_version: 2.0.0-alpha.5
    s3-only:
      kustomization_paths:
        - awsconfigs/apps/pipeline/s3
      output_helm_chart_path: charts/apps/kubeflow-pipelines/s3-only
      version: 0.1.1
      app_version: 2.0.0-alpha.5
```

Step 2. Define kubeflow component config dictionary (tools/helmify/template/values_config.yaml)

Step 3. Run Script with `PYTHONPATH=. python tools/helmify/src/kustomize_to_helm_automation.py`

Step 4. Check if potential failed yaml files exist in `tools/helmify/generated_output/helm_chart_temp_output_files`

## How the tool works
The Tool generated the helm charts with the following workflow:
1. Check if the component has multiple deployment options, if yes the chart path will be embedded with subfolders.
2. Configure `params.env` files based on the component dictionary `tools/helmify/template/values_config.yaml` before running `kustomize build`. (example: `awsconfigs/common/istio-ingress/overlays/cognito/params.env`)
3. Generate kustomized consolidated files based on the paths defined, and store the outputs in `tools/helmify/generated_output/kustomized_output_files/<chart_name>`.
4. Split the generated kustomized files into individual yaml files and organized into folders based on `Kind`.
5. Create helm charts with `helm create`, clean up unnecessary template files, update chart versions. 
6. Write `values.yaml` file inside the chart with infomation defined in `tools/helmify/template/values_config.yaml`, otherwise the values.yaml will be null.
7. Find potential failed yaml files in the previously generated splitted yaml files (syntax error such as the yaml file defination involves `{{ }}`)
8. Moved the splitted files into corresponding chart folders if no issues are found, otherwise the chart contents remain in `tools/helmify/generated_output/helm_chart_temp_output_files` for developer to verify.


## Help & Feedback

For help, please consider the following venues (in order):

* [Documentation](https://awslabs.github.io/kubeflow-manifests/docs/)
* [Search open issues](https://github.com/awslabs/kubeflow-manifests/issues)
* [File an issue](https://github.com/awslabs/kubeflow-manifests/issues/new/choose)
* Chat with us on the `#platform-aws` channel in the [Kubeflow Slack](https://www.kubeflow.org/docs/about/community/#slack) community.

## Contributing

We welcome community contributions and pull requests.

See our [contribution guide](CONTRIBUTING.md) for more information on how to
report issues, set up a development environment, and submit code.

We adhere to the [Amazon Open Source Code of Conduct](CODE_OF_CONDUCT.md#code-of-conduct).

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This project is [licensed](LICENSE) under the Apache-2.0 License.

