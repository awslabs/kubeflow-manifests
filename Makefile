SHELL := /bin/bash # Use bash syntax

install-awscli:
	curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
	unzip -o -q awscliv2.zip
	sudo ./aws/install --update
	rm -r ./aws
	rm -r awscliv2.zip
	aws --version

install-eksctl:
	$(eval EKSCTL_VERSION:=v0.137.0)
	curl --silent --location "https://github.com/weaveworks/eksctl/releases/download/$(EKSCTL_VERSION)/eksctl_Linux_amd64.tar.gz" | tar xz -C /tmp
	sudo mv /tmp/eksctl /usr/local/bin
	eksctl version

install-kubectl:
	$(eval KUBECTL_VERSION:=v1.25.0)
	curl -LO "https://dl.k8s.io/release/$(KUBECTL_VERSION)/bin/linux/amd64/kubectl"
	sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
	rm kubectl
	kubectl version --client

install-kustomize:
	$(eval KUSTOMIZE_VERSION:=5.0.1)
	curl --silent --location "https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv$(KUSTOMIZE_VERSION)/kustomize_v$(KUSTOMIZE_VERSION)_linux_amd64.tar.gz" | tar xz -C /tmp
	chmod +x /tmp/kustomize
	sudo mv /tmp/kustomize /usr/local/bin/kustomize
	kustomize version

install-yq:
	$(eval YQ_VERSION:=v4.26.1)
	curl --silent --location "https://github.com/mikefarah/yq/releases/download/${YQ_VERSION}/yq_linux_amd64.tar.gz" | tar xz -C /tmp
	sudo mv /tmp/yq_linux_amd64 /usr/bin/yq
	rm /tmp/install-man-page.sh
	rm /tmp/yq.1
	yq --version

install-jq:
	sudo apt-get install jq -y

install-terraform:
	$(eval TERRAFORM_VERSION:=1.4.5)
	curl "https://releases.hashicorp.com/terraform/$(TERRAFORM_VERSION)/terraform_$(TERRAFORM_VERSION)_linux_amd64.zip" -o "terraform.zip"
	unzip -o -q terraform.zip
	sudo install -o root -g root -m 0755 terraform /usr/local/bin/terraform
	rm terraform.zip
	rm terraform
	terraform --version

install-helm: 
	curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
	helm version

install-python:
	sudo apt install -q python3.8 -y 
	sudo apt install -q python3-pip -y
	python3.8 -m pip install --upgrade pip

install-python-packages:
	python3.8 -m pip install -r tests/e2e/requirements.txt

install-tools: install-awscli install-eksctl install-kubectl install-kustomize install-yq install-jq install-terraform install-helm install-python install-python-packages

verify-cluster-variables:
	test $(CLUSTER_NAME) || (echo Please export CLUSTER_NAME variable ; exit 1)
	test $(CLUSTER_REGION) || (echo Please export CLUSTER_REGION variable ; exit 1)

create-eks-cluster: verify-cluster-variables
	eksctl create cluster \
	--name $(CLUSTER_NAME) \
	--version 1.25 \
	--region $(CLUSTER_REGION) \
	--nodegroup-name linux-nodes \
	--node-type m5.xlarge \
	--nodes 5 \
	--nodes-min 5 \
	--nodes-max 10 \
	--managed \
	--with-oidc

connect-to-eks-cluster: verify-cluster-variables
	aws eks update-kubeconfig --name $(CLUSTER_NAME) --region $(CLUSTER_REGION)

port-forward:
	$(eval IP_ADDRESS:=127.0.0.1)
	$(eval PORT:=8080)
	kubectl port-forward svc/istio-ingressgateway --address $(IP_ADDRESS) -n istio-system $(PORT):80

bootstrap-ack: verify-cluster-variables connect-to-eks-cluster
	yq e '.cluster.name=env(CLUSTER_NAME)' -i tests/e2e/utils/ack_sm_controller_bootstrap/config.yaml
	yq e '.cluster.region=env(CLUSTER_REGION)' -i tests/e2e/utils/ack_sm_controller_bootstrap/config.yaml
	cd tests/e2e && PYTHONPATH=.. python3.8 utils/ack_sm_controller_bootstrap/setup_sm_controller_req.py

cleanup-ack-req: verify-cluster-variables
	yq e '.cluster.name=env(CLUSTER_NAME)' -i tests/e2e/utils/ack_sm_controller_bootstrap/config.yaml
	yq e '.cluster.region=env(CLUSTER_REGION)' -i tests/e2e/utils/ack_sm_controller_bootstrap/config.yaml
	cd tests/e2e && PYTHONPATH=.. python3.8 utils/ack_sm_controller_bootstrap/cleanup_sm_controller_req.py

deploy-kubeflow: bootstrap-ack
	$(eval DEPLOYMENT_OPTION:=vanilla)
	$(eval INSTALLATION_OPTION:=kustomize)
	$(eval PIPELINE_S3_CREDENTIAL_OPTION:=irsa)
	cd tests/e2e && PYTHONPATH=.. python3.8 utils/kubeflow_installation.py --deployment_option $(DEPLOYMENT_OPTION) --installation_option $(INSTALLATION_OPTION) --pipeline_s3_credential_option $(PIPELINE_S3_CREDENTIAL_OPTION) --cluster_name $(CLUSTER_NAME)

delete-kubeflow:
	$(eval DEPLOYMENT_OPTION:=vanilla)
	$(eval INSTALLATION_OPTION:=kustomize)
	cd tests/e2e && PYTHONPATH=.. python3.8 utils/kubeflow_uninstallation.py --deployment_option $(DEPLOYMENT_OPTION) --installation_option $(INSTALLATION_OPTION)

helmify:
	PYTHONPATH=. python3.8 tools/helmify/src/kustomize_to_helm_automation.py