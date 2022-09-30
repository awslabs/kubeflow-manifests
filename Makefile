SHELL := /bin/bash # Use bash syntax

export CLUSTER_REGION=us-west-1
export CLUSTER_NAME=mlp-eks
export KUBECONFIG=~/.kube/eksctl.cfg
export S3_BUCKET=mlp-mlops-kubeflow
export DB_INSTANCE_NAME=mlp-mlops-mysql
export AWS_ACCESS_KEY_ID=
export AWS_SECRET_ACCESS_KEY=
export MINIO_AWS_ACCESS_KEY_ID=
export MINIO_AWS_SECRET_ACCESS_KEY=
export RDS_SECRET_NAME=mlp-mlops-rds-secret-4
export S3_SECRET_NAME=mlp-mlops-s3-secret-4

install-awscli:
	curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
	unzip -o -q awscliv2.zip
	sudo ./aws/install --update
	rm -r ./aws
	rm -r awscliv2.zip
	aws --version

install-eksctl:
	$(eval EKSCTL_VERSION:=v0.111.0)
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
	$(eval KUSTOMIZE_VERSION:=3.2.0)
	wget https://github.com/kubernetes-sigs/kustomize/releases/download/v$(KUSTOMIZE_VERSION)/kustomize_$(KUSTOMIZE_VERSION)_linux_amd64
	chmod +x kustomize_$(KUSTOMIZE_VERSION)_linux_amd64
	sudo mv kustomize_$(KUSTOMIZE_VERSION)_linux_amd64 /usr/local/bin/kustomize
	kustomize version

install-yq:
	$(eval YQ_VERSION:=v4.26.1)
	wget https://github.com/mikefarah/yq/releases/download/${YQ_VERSION}/yq_linux_amd64.tar.gz -O - | tar xz
	sudo mv yq_linux_amd64 /usr/bin/yq
	rm install-man-page.sh
	rm yq.1
	yq --version

install-jq:
	$(eval JQ_VERSION:=1.5+dfsg-2)
	sudo apt-get install jq=$(JQ_VERSION) -y

install-terraform:
	$(eval TERRAFORM_VERSION:=1.2.7)
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
	--version 1.22 \
	--region $(CLUSTER_REGION) \
	--nodegroup-name linux-nodes \
	--node-type m5.xlarge \
	--nodes 5 \
	--nodes-min 5 \
	--nodes-max 10 \
	--managed \
	--with-oidc

delete-eks-cluster: verify-cluster-variables
	eksctl delete cluster \
	--name $(CLUSTER_NAME) \
	--region $(CLUSTER_REGION)

create-rds-s3: verify-cluster-variables
	cd tests/e2e && PYTHONPATH=.. python3.8 utils/rds-s3/auto-rds-s3-setup.py \
	--cluster $(CLUSTER_NAME) \
	--region $(CLUSTER_REGION) \
	--bucket $(S3_BUCKET) \
	--s3_aws_access_key_id $(MINIO_AWS_ACCESS_KEY_ID) \
	--s3_aws_secret_access_key $(MINIO_AWS_SECRET_ACCESS_KEY) \
	--db_instance_name $(DB_INSTANCE_NAME) \
	--s3_secret_name $(S3_SECRET_NAME) \
	--rds_secret_name $(RDS_SECRET_NAME)

delete-rds-s3: verify-cluster-variables
	cd tests/e2e && PYTHONPATH=.. python3.8 utils/rds-s3/auto-rds-s3-cleanup.py

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
	$(eval DEPLOYMENT_OPTION:=rds-s3)
	$(eval INSTALLATION_OPTION:=helm)
	cd tests/e2e && PYTHONPATH=.. python3.8 utils/kubeflow_installation.py --deployment_option $(DEPLOYMENT_OPTION) --installation_option $(INSTALLATION_OPTION) --cluster_name $(CLUSTER_NAME)

delete-kubeflow:
	$(eval DEPLOYMENT_OPTION:=rds-s3)
	$(eval INSTALLATION_OPTION:=helm)
	cd tests/e2e && PYTHONPATH=.. python3.8 utils/kubeflow_uninstallation.py --deployment_option $(DEPLOYMENT_OPTION) --installation_option $(INSTALLATION_OPTION)

bootstrap-alb: verify-cluster-variables connect-to-eks-cluster
	yq e '.cluster.name=env(CLUSTER_NAME)' -i tests/e2e/utils/load_balancer/config.yaml
	yq e '.cluster.region=env(CLUSTER_REGION)' -i tests/e2e/utils/load_balancer/config.yaml
	cd tests/e2e && PYTHONPATH=.. python3.8 utils/load_balancer/setup_load_balancer.py

cleanup-alb: verify-cluster-variables
	yq e '.cluster.name=env(CLUSTER_NAME)' -i tests/e2e/utils/load_balancer/config.yaml
	yq e '.cluster.region=env(CLUSTER_REGION)' -i tests/e2e/utils/load_balancer/config.yaml
	cd tests/e2e && PYTHONPATH=.. python3.8 utils/load_balancer/lb_resources_cleanup.py

test:
	echo $(MINIO_AWS_ACCESS_KEY_ID)