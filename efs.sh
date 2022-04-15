export CLUSTER_NAME=bugbash-6
export CLUSTER_REGION=us-west-1
export FILESYSTEM_NAME=m-bugbash-6-fs-7
export SG_NAME=m-bugbash-6-sg-7
cd tests/e2e
python utils/auto-efs-setup.py --region $CLUSTER_REGION --cluster $CLUSTER_NAME --efs_file_system_name $FILESYSTEM_NAME --efs_security_group_name $SG_NAME
export file_system_id=fs-0
kfd
cd docs/deployment/add-ons/storage/efs
file_system_id=$file_system_id yq e '.parameters.fileSystemId = env(file_system_id)' -i dynamic-provisioning/sc.yaml
export PVC_NAMESPACE=kubeflow-user-example-com
kubectl patch storageclass gp2 -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'
kubectl patch storageclass efs-sc -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
export CLAIM_NAME=efs-claim-m-bugbash-6-7
cd ..
yq e '.metadata.name = env(CLAIM_NAME)' -i notebook-sample/set-permission-job.yaml
yq e '.metadata.namespace = env(PVC_NAMESPACE)' -i notebook-sample/set-permission-job.yaml
yq e '.spec.template.spec.volumes[0].persistentVolumeClaim.claimName = env(CLAIM_NAME)' -i notebook-sample/set-permission-job.yaml
kubectl apply -f notebook-sample/set-permission-job.yaml
cd efs
yq e '.metadata.namespace = env(PVC_NAMESPACE)' -i dynamic-provisioning/pvc.yaml
yq e '.metadata.name = env(CLAIM_NAME)' -i dynamic-provisioning/pvc.yaml
k apply -f dynamic-provisioning/pvc.yaml


# k describe pod -n kubeflow-user-example-com efs-claim-m-bugbash-6-v27ls
# k get pvc -n kubeflow-user-example-com
# k describe pvc -n kubeflow-user-example-com efs-claim-m-bugbash-6

