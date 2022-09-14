## How to run `split_kfp_for_terraform_helm.py`

```sh
~/kf/helm-1-6-official/kubeflow-manifests/charts/utils helm-chart-vanilla-v1.6.0
$ python3 split_kfp_for_terraform_helm.py --help
usage: split_kfp_for_terraform_helm.py [-h] [--helm-chart-folder HELM_CHART_FOLDER] [--overwrite OVERWRITE]

Split KFP helm charts since terraform fails with helm charts of a certain size.

optional arguments:
  -h, --help            show this help message and exit
  --helm-chart-folder HELM_CHART_FOLDER
                        helm chart folder
  --overwrite OVERWRITE
                        recreates the folders if they already exist
```

### Example split KFP vanilla
```sh
python3 split_kfp_for_terraform_helm.py --helm-chart-folder ../apps/kubeflow-pipelines/vanilla
```

Output:
```sh
$ tree ../apps/kubeflow-pipelines

../apps/kubeflow-pipelines
├── vanilla
│   ├── Chart.yaml
│   ├── crds
│   │   ├── clusterworkflowtemplates.argoproj.io-CustomResourceDefinition.yaml
│   │   ├── compositecontrollers.metacontroller.k8s.io-CustomResourceDefinition.yaml
│   │   ├── controllerrevisions.metacontroller.k8s.io-CustomResourceDefinition.yaml
│   │   ├── cronworkflows.argoproj.io-CustomResourceDefinition.yaml
│   │   ├── decoratorcontrollers.metacontroller.k8s.io-CustomResourceDefinition.yaml
│   │   ├── scheduledworkflows.kubeflow.org-CustomResourceDefinition.yaml
│   │   ├── viewers.kubeflow.org-CustomResourceDefinition.yaml
│   │   ├── workfloweventbindings.argoproj.io-CustomResourceDefinition.yaml
│   │   ├── workflows.argoproj.io-CustomResourceDefinition.yaml
│   │   ├── workflowtaskresults.argoproj.io-CustomResourceDefinition.yaml
│   │   ├── workflowtasksets.argoproj.io-CustomResourceDefinition.yaml
│   │   └── workflowtemplates.argoproj.io-CustomResourceDefinition.yaml
│   ├── templates
│   │   ├── AuthorizationPolicy
│   │   │   ├── metadata-grpc-service-kubeflow-AuthorizationPolicy.yaml
│   │   │   ├── minio-service-kubeflow-AuthorizationPolicy.yaml
│   │   │   ├── ml-pipeline-kubeflow-AuthorizationPolicy.yaml
│   │   │   ├── ml-pipeline-ui-kubeflow-AuthorizationPolicy.yaml
│   │   │   ├── ml-pipeline-visualizationserver-kubeflow-AuthorizationPolicy.yaml
│   │   │   ├── mysql-kubeflow-AuthorizationPolicy.yaml
│   │   │   └── service-cache-server-kubeflow-AuthorizationPolicy.yaml
│   │   ├── Certificate
│   │   │   └── kfp-cache-cert-kubeflow-Certificate.yaml
│   │   ├── ClusterRole
│   │   │   ├── aggregate-to-kubeflow-pipelines-edit-ClusterRole.yaml
│   │   │   ├── aggregate-to-kubeflow-pipelines-view-ClusterRole.yaml
│   │   │   ├── argo-aggregate-to-admin-ClusterRole.yaml
│   │   │   ├── argo-aggregate-to-edit-ClusterRole.yaml
│   │   │   ├── argo-aggregate-to-view-ClusterRole.yaml
│   │   │   ├── argo-cluster-role-ClusterRole.yaml
│   │   │   ├── kubeflow-pipelines-cache-role-ClusterRole.yaml
│   │   │   ├── kubeflow-pipelines-edit-ClusterRole.yaml
│   │   │   ├── kubeflow-pipelines-metadata-writer-role-ClusterRole.yaml
│   │   │   ├── kubeflow-pipelines-view-ClusterRole.yaml
│   │   │   ├── ml-pipeline-ClusterRole.yaml
│   │   │   ├── ml-pipeline-persistenceagent-role-ClusterRole.yaml
│   │   │   ├── ml-pipeline-scheduledworkflow-role-ClusterRole.yaml
│   │   │   ├── ml-pipeline-ui-ClusterRole.yaml
│   │   │   └── ml-pipeline-viewer-controller-role-ClusterRole.yaml
│   │   ├── ClusterRoleBinding
│   │   │   ├── argo-binding-ClusterRoleBinding.yaml
│   │   │   ├── kubeflow-pipelines-cache-binding-ClusterRoleBinding.yaml
│   │   │   ├── kubeflow-pipelines-metadata-writer-binding-ClusterRoleBinding.yaml
│   │   │   ├── meta-controller-cluster-role-binding-ClusterRoleBinding.yaml
│   │   │   ├── ml-pipeline-ClusterRoleBinding.yaml
│   │   │   ├── ml-pipeline-persistenceagent-binding-ClusterRoleBinding.yaml
│   │   │   ├── ml-pipeline-scheduledworkflow-binding-ClusterRoleBinding.yaml
│   │   │   ├── ml-pipeline-ui-ClusterRoleBinding.yaml
│   │   │   └── ml-pipeline-viewer-crd-binding-ClusterRoleBinding.yaml
│   │   ├── CompositeController
│   │   │   └── kubeflow-pipelines-profile-controller-kubeflow-CompositeController.yaml
│   │   ├── ConfigMap
│   │   │   ├── kfp-launcher-kubeflow-ConfigMap.yaml
│   │   │   ├── kubeflow-pipelines-profile-controller-code-btcch948fc-kubeflow-ConfigMap.yaml
│   │   │   ├── kubeflow-pipelines-profile-controller-env-mgh6th2gff-kubeflow-ConfigMap.yaml
│   │   │   ├── metadata-grpc-configmap-kubeflow-ConfigMap.yaml
│   │   │   ├── ml-pipeline-ui-configmap-kubeflow-ConfigMap.yaml
│   │   │   ├── pipeline-api-server-config-f4t72426kt-kubeflow-ConfigMap.yaml
│   │   │   ├── pipeline-install-config-kubeflow-ConfigMap.yaml
│   │   │   └── workflow-controller-configmap-kubeflow-ConfigMap.yaml
│   │   ├── Deployment
│   │   │   ├── cache-server-kubeflow-Deployment.yaml
│   │   │   ├── kubeflow-pipelines-profile-controller-kubeflow-Deployment.yaml
│   │   │   ├── metadata-envoy-deployment-kubeflow-Deployment.yaml
│   │   │   ├── metadata-grpc-deployment-kubeflow-Deployment.yaml
│   │   │   ├── metadata-writer-kubeflow-Deployment.yaml
│   │   │   ├── minio-kubeflow-Deployment.yaml
│   │   │   ├── ml-pipeline-kubeflow-Deployment.yaml
│   │   │   ├── ml-pipeline-persistenceagent-kubeflow-Deployment.yaml
│   │   │   ├── ml-pipeline-scheduledworkflow-kubeflow-Deployment.yaml
│   │   │   ├── ml-pipeline-ui-kubeflow-Deployment.yaml
│   │   │   ├── ml-pipeline-viewer-crd-kubeflow-Deployment.yaml
│   │   │   ├── ml-pipeline-visualizationserver-kubeflow-Deployment.yaml
│   │   │   ├── mysql-kubeflow-Deployment.yaml
│   │   │   └── workflow-controller-kubeflow-Deployment.yaml
│   │   ├── DestinationRule
│   │   │   ├── metadata-grpc-service-kubeflow-DestinationRule.yaml
│   │   │   ├── ml-pipeline-kubeflow-DestinationRule.yaml
│   │   │   ├── ml-pipeline-minio-kubeflow-DestinationRule.yaml
│   │   │   ├── ml-pipeline-mysql-kubeflow-DestinationRule.yaml
│   │   │   ├── ml-pipeline-ui-kubeflow-DestinationRule.yaml
│   │   │   └── ml-pipeline-visualizationserver-kubeflow-DestinationRule.yaml
│   │   ├── Issuer
│   │   │   └── kfp-cache-selfsigned-issuer-kubeflow-Issuer.yaml
│   │   ├── MutatingWebhookConfiguration
│   │   │   └── cache-webhook-kubeflow-MutatingWebhookConfiguration.yaml
│   │   ├── PersistentVolumeClaim
│   │   │   ├── minio-pvc-kubeflow-PersistentVolumeClaim.yaml
│   │   │   └── mysql-pv-claim-kubeflow-PersistentVolumeClaim.yaml
│   │   ├── PriorityClass
│   │   │   └── workflow-controller-PriorityClass.yaml
│   │   ├── Role
│   │   │   ├── argo-role-kubeflow-Role.yaml
│   │   │   ├── kubeflow-pipelines-cache-role-kubeflow-Role.yaml
│   │   │   ├── kubeflow-pipelines-metadata-writer-role-kubeflow-Role.yaml
│   │   │   ├── ml-pipeline-kubeflow-Role.yaml
│   │   │   ├── ml-pipeline-persistenceagent-role-kubeflow-Role.yaml
│   │   │   ├── ml-pipeline-scheduledworkflow-role-kubeflow-Role.yaml
│   │   │   ├── ml-pipeline-ui-kubeflow-Role.yaml
│   │   │   ├── ml-pipeline-viewer-controller-role-kubeflow-Role.yaml
│   │   │   └── pipeline-runner-kubeflow-Role.yaml
│   │   ├── RoleBinding
│   │   │   ├── argo-binding-kubeflow-RoleBinding.yaml
│   │   │   ├── kubeflow-pipelines-cache-binding-kubeflow-RoleBinding.yaml
│   │   │   ├── kubeflow-pipelines-metadata-writer-binding-kubeflow-RoleBinding.yaml
│   │   │   ├── ml-pipeline-kubeflow-RoleBinding.yaml
│   │   │   ├── ml-pipeline-persistenceagent-binding-kubeflow-RoleBinding.yaml
│   │   │   ├── ml-pipeline-scheduledworkflow-binding-kubeflow-RoleBinding.yaml
│   │   │   ├── ml-pipeline-ui-kubeflow-RoleBinding.yaml
│   │   │   ├── ml-pipeline-viewer-crd-binding-kubeflow-RoleBinding.yaml
│   │   │   └── pipeline-runner-binding-kubeflow-RoleBinding.yaml
│   │   ├── Secret
│   │   │   ├── mlpipeline-minio-artifact-kubeflow-Secret.yaml
│   │   │   └── mysql-secret-kubeflow-Secret.yaml
│   │   ├── Service
│   │   │   ├── cache-server-kubeflow-Service.yaml
│   │   │   ├── kubeflow-pipelines-profile-controller-kubeflow-Service.yaml
│   │   │   ├── metadata-envoy-service-kubeflow-Service.yaml
│   │   │   ├── metadata-grpc-service-kubeflow-Service.yaml
│   │   │   ├── minio-service-kubeflow-Service.yaml
│   │   │   ├── ml-pipeline-kubeflow-Service.yaml
│   │   │   ├── ml-pipeline-ui-kubeflow-Service.yaml
│   │   │   ├── ml-pipeline-visualizationserver-kubeflow-Service.yaml
│   │   │   ├── mysql-kubeflow-Service.yaml
│   │   │   └── workflow-controller-metrics-kubeflow-Service.yaml
│   │   ├── ServiceAccount
│   │   │   ├── argo-kubeflow-ServiceAccount.yaml
│   │   │   ├── kubeflow-pipelines-cache-kubeflow-ServiceAccount.yaml
│   │   │   ├── kubeflow-pipelines-container-builder-kubeflow-ServiceAccount.yaml
│   │   │   ├── kubeflow-pipelines-metadata-writer-kubeflow-ServiceAccount.yaml
│   │   │   ├── kubeflow-pipelines-viewer-kubeflow-ServiceAccount.yaml
│   │   │   ├── meta-controller-service-kubeflow-ServiceAccount.yaml
│   │   │   ├── metadata-grpc-server-kubeflow-ServiceAccount.yaml
│   │   │   ├── ml-pipeline-kubeflow-ServiceAccount.yaml
│   │   │   ├── ml-pipeline-persistenceagent-kubeflow-ServiceAccount.yaml
│   │   │   ├── ml-pipeline-scheduledworkflow-kubeflow-ServiceAccount.yaml
│   │   │   ├── ml-pipeline-ui-kubeflow-ServiceAccount.yaml
│   │   │   ├── ml-pipeline-viewer-crd-service-account-kubeflow-ServiceAccount.yaml
│   │   │   ├── ml-pipeline-visualizationserver-kubeflow-ServiceAccount.yaml
│   │   │   ├── mysql-kubeflow-ServiceAccount.yaml
│   │   │   └── pipeline-runner-kubeflow-ServiceAccount.yaml
│   │   ├── StatefulSet
│   │   │   └── metacontroller-kubeflow-StatefulSet.yaml
│   │   ├── VirtualService
│   │   │   ├── metadata-grpc-kubeflow-VirtualService.yaml
│   │   │   └── ml-pipeline-ui-kubeflow-VirtualService.yaml
│   │   └── _helpers.tpl
│   └── values.yaml
├── vanilla-part-1
│   ├── Chart.yaml
│   ├── crds
│   │   ├── clusterworkflowtemplates.argoproj.io-CustomResourceDefinition.yaml
│   │   ├── compositecontrollers.metacontroller.k8s.io-CustomResourceDefinition.yaml
│   │   ├── controllerrevisions.metacontroller.k8s.io-CustomResourceDefinition.yaml
│   │   ├── cronworkflows.argoproj.io-CustomResourceDefinition.yaml
│   │   ├── decoratorcontrollers.metacontroller.k8s.io-CustomResourceDefinition.yaml
│   │   ├── scheduledworkflows.kubeflow.org-CustomResourceDefinition.yaml
│   │   ├── viewers.kubeflow.org-CustomResourceDefinition.yaml
│   │   ├── workfloweventbindings.argoproj.io-CustomResourceDefinition.yaml
│   │   ├── workflows.argoproj.io-CustomResourceDefinition.yaml
│   │   ├── workflowtaskresults.argoproj.io-CustomResourceDefinition.yaml
│   │   ├── workflowtasksets.argoproj.io-CustomResourceDefinition.yaml
│   │   └── workflowtemplates.argoproj.io-CustomResourceDefinition.yaml
│   ├── templates
│   │   ├── Certificate
│   │   │   └── kfp-cache-cert-kubeflow-Certificate.yaml
│   │   ├── ClusterRole
│   │   │   ├── aggregate-to-kubeflow-pipelines-edit-ClusterRole.yaml
│   │   │   ├── aggregate-to-kubeflow-pipelines-view-ClusterRole.yaml
│   │   │   ├── argo-aggregate-to-admin-ClusterRole.yaml
│   │   │   ├── argo-aggregate-to-edit-ClusterRole.yaml
│   │   │   ├── argo-aggregate-to-view-ClusterRole.yaml
│   │   │   ├── argo-cluster-role-ClusterRole.yaml
│   │   │   ├── kubeflow-pipelines-cache-role-ClusterRole.yaml
│   │   │   ├── kubeflow-pipelines-edit-ClusterRole.yaml
│   │   │   ├── kubeflow-pipelines-metadata-writer-role-ClusterRole.yaml
│   │   │   ├── kubeflow-pipelines-view-ClusterRole.yaml
│   │   │   ├── ml-pipeline-ClusterRole.yaml
│   │   │   ├── ml-pipeline-persistenceagent-role-ClusterRole.yaml
│   │   │   ├── ml-pipeline-scheduledworkflow-role-ClusterRole.yaml
│   │   │   ├── ml-pipeline-ui-ClusterRole.yaml
│   │   │   └── ml-pipeline-viewer-controller-role-ClusterRole.yaml
│   │   ├── ClusterRoleBinding
│   │   │   ├── argo-binding-ClusterRoleBinding.yaml
│   │   │   ├── kubeflow-pipelines-cache-binding-ClusterRoleBinding.yaml
│   │   │   ├── kubeflow-pipelines-metadata-writer-binding-ClusterRoleBinding.yaml
│   │   │   ├── meta-controller-cluster-role-binding-ClusterRoleBinding.yaml
│   │   │   ├── ml-pipeline-ClusterRoleBinding.yaml
│   │   │   ├── ml-pipeline-persistenceagent-binding-ClusterRoleBinding.yaml
│   │   │   ├── ml-pipeline-scheduledworkflow-binding-ClusterRoleBinding.yaml
│   │   │   ├── ml-pipeline-ui-ClusterRoleBinding.yaml
│   │   │   └── ml-pipeline-viewer-crd-binding-ClusterRoleBinding.yaml
│   │   ├── ConfigMap
│   │   │   ├── kfp-launcher-kubeflow-ConfigMap.yaml
│   │   │   ├── kubeflow-pipelines-profile-controller-code-btcch948fc-kubeflow-ConfigMap.yaml
│   │   │   ├── kubeflow-pipelines-profile-controller-env-mgh6th2gff-kubeflow-ConfigMap.yaml
│   │   │   ├── metadata-grpc-configmap-kubeflow-ConfigMap.yaml
│   │   │   ├── ml-pipeline-ui-configmap-kubeflow-ConfigMap.yaml
│   │   │   ├── pipeline-api-server-config-f4t72426kt-kubeflow-ConfigMap.yaml
│   │   │   ├── pipeline-install-config-kubeflow-ConfigMap.yaml
│   │   │   └── workflow-controller-configmap-kubeflow-ConfigMap.yaml
│   │   ├── Issuer
│   │   │   └── kfp-cache-selfsigned-issuer-kubeflow-Issuer.yaml
│   │   ├── MutatingWebhookConfiguration
│   │   │   └── cache-webhook-kubeflow-MutatingWebhookConfiguration.yaml
│   │   ├── PriorityClass
│   │   │   └── workflow-controller-PriorityClass.yaml
│   │   ├── Role
│   │   │   ├── argo-role-kubeflow-Role.yaml
│   │   │   ├── kubeflow-pipelines-cache-role-kubeflow-Role.yaml
│   │   │   ├── kubeflow-pipelines-metadata-writer-role-kubeflow-Role.yaml
│   │   │   ├── ml-pipeline-kubeflow-Role.yaml
│   │   │   ├── ml-pipeline-persistenceagent-role-kubeflow-Role.yaml
│   │   │   ├── ml-pipeline-scheduledworkflow-role-kubeflow-Role.yaml
│   │   │   ├── ml-pipeline-ui-kubeflow-Role.yaml
│   │   │   ├── ml-pipeline-viewer-controller-role-kubeflow-Role.yaml
│   │   │   └── pipeline-runner-kubeflow-Role.yaml
│   │   ├── RoleBinding
│   │   │   ├── argo-binding-kubeflow-RoleBinding.yaml
│   │   │   ├── kubeflow-pipelines-cache-binding-kubeflow-RoleBinding.yaml
│   │   │   ├── kubeflow-pipelines-metadata-writer-binding-kubeflow-RoleBinding.yaml
│   │   │   ├── ml-pipeline-kubeflow-RoleBinding.yaml
│   │   │   ├── ml-pipeline-persistenceagent-binding-kubeflow-RoleBinding.yaml
│   │   │   ├── ml-pipeline-scheduledworkflow-binding-kubeflow-RoleBinding.yaml
│   │   │   ├── ml-pipeline-ui-kubeflow-RoleBinding.yaml
│   │   │   ├── ml-pipeline-viewer-crd-binding-kubeflow-RoleBinding.yaml
│   │   │   └── pipeline-runner-binding-kubeflow-RoleBinding.yaml
│   │   ├── Secret
│   │   │   ├── mlpipeline-minio-artifact-kubeflow-Secret.yaml
│   │   │   └── mysql-secret-kubeflow-Secret.yaml
│   │   ├── Service
│   │   │   ├── cache-server-kubeflow-Service.yaml
│   │   │   ├── kubeflow-pipelines-profile-controller-kubeflow-Service.yaml
│   │   │   ├── metadata-envoy-service-kubeflow-Service.yaml
│   │   │   ├── metadata-grpc-service-kubeflow-Service.yaml
│   │   │   ├── minio-service-kubeflow-Service.yaml
│   │   │   ├── ml-pipeline-kubeflow-Service.yaml
│   │   │   ├── ml-pipeline-ui-kubeflow-Service.yaml
│   │   │   ├── ml-pipeline-visualizationserver-kubeflow-Service.yaml
│   │   │   ├── mysql-kubeflow-Service.yaml
│   │   │   └── workflow-controller-metrics-kubeflow-Service.yaml
│   │   ├── ServiceAccount
│   │   │   ├── argo-kubeflow-ServiceAccount.yaml
│   │   │   ├── kubeflow-pipelines-cache-kubeflow-ServiceAccount.yaml
│   │   │   ├── kubeflow-pipelines-container-builder-kubeflow-ServiceAccount.yaml
│   │   │   ├── kubeflow-pipelines-metadata-writer-kubeflow-ServiceAccount.yaml
│   │   │   ├── kubeflow-pipelines-viewer-kubeflow-ServiceAccount.yaml
│   │   │   ├── meta-controller-service-kubeflow-ServiceAccount.yaml
│   │   │   ├── metadata-grpc-server-kubeflow-ServiceAccount.yaml
│   │   │   ├── ml-pipeline-kubeflow-ServiceAccount.yaml
│   │   │   ├── ml-pipeline-persistenceagent-kubeflow-ServiceAccount.yaml
│   │   │   ├── ml-pipeline-scheduledworkflow-kubeflow-ServiceAccount.yaml
│   │   │   ├── ml-pipeline-ui-kubeflow-ServiceAccount.yaml
│   │   │   ├── ml-pipeline-viewer-crd-service-account-kubeflow-ServiceAccount.yaml
│   │   │   ├── ml-pipeline-visualizationserver-kubeflow-ServiceAccount.yaml
│   │   │   ├── mysql-kubeflow-ServiceAccount.yaml
│   │   │   └── pipeline-runner-kubeflow-ServiceAccount.yaml
│   │   ├── VirtualService
│   │   │   ├── metadata-grpc-kubeflow-VirtualService.yaml
│   │   │   └── ml-pipeline-ui-kubeflow-VirtualService.yaml
│   │   └── _helpers.tpl
│   └── values.yaml
└── vanilla-part-2
    ├── Chart.yaml
    ├── crds
    │   ├── clusterworkflowtemplates.argoproj.io-CustomResourceDefinition.yaml
    │   ├── compositecontrollers.metacontroller.k8s.io-CustomResourceDefinition.yaml
    │   ├── controllerrevisions.metacontroller.k8s.io-CustomResourceDefinition.yaml
    │   ├── cronworkflows.argoproj.io-CustomResourceDefinition.yaml
    │   ├── decoratorcontrollers.metacontroller.k8s.io-CustomResourceDefinition.yaml
    │   ├── scheduledworkflows.kubeflow.org-CustomResourceDefinition.yaml
    │   ├── viewers.kubeflow.org-CustomResourceDefinition.yaml
    │   ├── workfloweventbindings.argoproj.io-CustomResourceDefinition.yaml
    │   ├── workflows.argoproj.io-CustomResourceDefinition.yaml
    │   ├── workflowtaskresults.argoproj.io-CustomResourceDefinition.yaml
    │   ├── workflowtasksets.argoproj.io-CustomResourceDefinition.yaml
    │   └── workflowtemplates.argoproj.io-CustomResourceDefinition.yaml
    ├── templates
    │   ├── AuthorizationPolicy
    │   │   ├── metadata-grpc-service-kubeflow-AuthorizationPolicy.yaml
    │   │   ├── minio-service-kubeflow-AuthorizationPolicy.yaml
    │   │   ├── ml-pipeline-kubeflow-AuthorizationPolicy.yaml
    │   │   ├── ml-pipeline-ui-kubeflow-AuthorizationPolicy.yaml
    │   │   ├── ml-pipeline-visualizationserver-kubeflow-AuthorizationPolicy.yaml
    │   │   ├── mysql-kubeflow-AuthorizationPolicy.yaml
    │   │   └── service-cache-server-kubeflow-AuthorizationPolicy.yaml
    │   ├── CompositeController
    │   │   └── kubeflow-pipelines-profile-controller-kubeflow-CompositeController.yaml
    │   ├── Deployment
    │   │   ├── cache-server-kubeflow-Deployment.yaml
    │   │   ├── kubeflow-pipelines-profile-controller-kubeflow-Deployment.yaml
    │   │   ├── metadata-envoy-deployment-kubeflow-Deployment.yaml
    │   │   ├── metadata-grpc-deployment-kubeflow-Deployment.yaml
    │   │   ├── metadata-writer-kubeflow-Deployment.yaml
    │   │   ├── minio-kubeflow-Deployment.yaml
    │   │   ├── ml-pipeline-kubeflow-Deployment.yaml
    │   │   ├── ml-pipeline-persistenceagent-kubeflow-Deployment.yaml
    │   │   ├── ml-pipeline-scheduledworkflow-kubeflow-Deployment.yaml
    │   │   ├── ml-pipeline-ui-kubeflow-Deployment.yaml
    │   │   ├── ml-pipeline-viewer-crd-kubeflow-Deployment.yaml
    │   │   ├── ml-pipeline-visualizationserver-kubeflow-Deployment.yaml
    │   │   ├── mysql-kubeflow-Deployment.yaml
    │   │   └── workflow-controller-kubeflow-Deployment.yaml
    │   ├── DestinationRule
    │   │   ├── metadata-grpc-service-kubeflow-DestinationRule.yaml
    │   │   ├── ml-pipeline-kubeflow-DestinationRule.yaml
    │   │   ├── ml-pipeline-minio-kubeflow-DestinationRule.yaml
    │   │   ├── ml-pipeline-mysql-kubeflow-DestinationRule.yaml
    │   │   ├── ml-pipeline-ui-kubeflow-DestinationRule.yaml
    │   │   └── ml-pipeline-visualizationserver-kubeflow-DestinationRule.yaml
    │   ├── PersistentVolumeClaim
    │   │   ├── minio-pvc-kubeflow-PersistentVolumeClaim.yaml
    │   │   └── mysql-pv-claim-kubeflow-PersistentVolumeClaim.yaml
    │   ├── StatefulSet
    │   │   └── metacontroller-kubeflow-StatefulSet.yaml
    │   └── _helpers.tpl
    └── values.yaml

47 directories, 273 files
```