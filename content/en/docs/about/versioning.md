+++
title = "Releases and Versioning"
description = "Familiarize yourself with Kubeflow on AWS release cadences and version naming conventions"
weight = 20
+++

This repository was created for the development of Kubeflow on AWS as described in the [Kubeflow distributions guidelines](https://github.com/kubeflow/community/blob/master/proposals/kubeflow-distributions.md). 

#### v1.3.1

Although the distribution manifests are hosted in this repository, many of the overlays and configuration files in this repository have a dependency on the manifests published by the Kubeflow community in the [kubeflow/manifests](https://github.com/kubeflow/manifests) repository. Hence, the AWS distribution of Kubeflow for v1.3.1 was developed on a [fork](https://github.com/awslabs/kubeflow-manifests/tree/v1.3-branch) of the `v1.3-branch` of the `kubeflow/manifests` repository. This presented several challenges for ongoing maintenance as described in [Issue #76](https://github.com/awslabs/kubeflow-manifests/issues/76). 

#### v1.4+

Starting with Kubeflow v1.4, the development of the AWS distribution of Kubeflow is done on the [`main`](https://github.com/awslabs/kubeflow-manifests/tree/main) branch. The `main` branch contains only the delta from the released manifests in the `kubeflow/manifests` repository and additional components required for the AWS distribution.

### Versioning

Kubeflow on AWS releases are built on top of Kubeflow releases and therefore use the following naming convention: `{KUBEFLOW_RELEASE_VERSION}-aws-b{BUILD_NUMBER}`.

* Ex: Kubeflow v1.3.1 on AWS version 1.0.0 will have the version `v1.3.1-aws-b1.0.0`.

`KUBEFLOW_RELEASE_VERSION` refers to [Kubeflow's released version](https://github.com/kubeflow/manifests/releases) and `BUILD_NUMBER` refers to the AWS build for that Kubeflow version. `BUILD_NUMBER` uses [semantic versioning](https://semver.org/) (SemVer) to indicate whether changes included in a particular release introduce features or bug fixes and whether or not features break backwards compatibility.

### Releases

When a version of Kubeflow on AWS is released, a Git tag with the naming convention `{KUBEFLOW_RELEASE_VERSION}-aws-b{BUILD_NUMBER}` is created. These releases can be found in the Kubeflow on AWS repository [releases](https://github.com/awslabs/kubeflow-manifests/releases) section.