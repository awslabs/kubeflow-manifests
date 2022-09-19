SHELL := /bin/bash # Use bash syntax

deploy: init \
 create-vpc \
 create-eks-cluster \
 deploy-eks-blueprints-k8s-addons \
 deploy-kubeflow-components

delete: delete-kubeflow-components \
 delete-eks-blueprints-k8s-addons \
 delete-eks-cluster \
 delete-vpc
	terraform destroy -auto-approve

init:
	terraform init


create-vpc:
	terraform apply -target="module.vpc" -auto-approve

create-eks-cluster:
	terraform apply -target="module.eks_blueprints" -auto-approve

deploy-eks-blueprints-k8s-addons:
	terraform apply -target="module.eks_blueprints_kubernetes_addons" -auto-approve

deploy-kubeflow-components:
	terraform apply -target="module.kubeflow_components" -auto-approve


delete-vpc:
	terraform destroy -target="module.vpc" -auto-approve

delete-eks-cluster:
	terraform destroy -target="module.eks_blueprints" -auto-approve

delete-eks-blueprints-k8s-addons:
	terraform destroy -target="module.eks_blueprints_kubernetes_addons" -auto-approve

delete-kubeflow-components:
# hack to handle the automatic deletion of the sa when calling helm delete 
# which causes deletion of the tf created sa to fail
# todo: profiles-and-kfam helm chart should accept an optional irsa role annotation
	terraform state rm "module.kubeflow_components.module.kubeflow_profiles_and_kfam.kubernetes_service_account_v1.profile_controller_sa" || true
	terraform destroy -target="module.kubeflow_components" -auto-approve

# don't create executables
.PHONY: *