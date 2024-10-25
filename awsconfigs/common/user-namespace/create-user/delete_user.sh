# namespace & profile to delete
export PROFILE_NAMESPACE=test-user2
export CLUSTER_REGION=us-east-1
export CLUSTER_NAME=kf
# delete rolebinding
kubectl delete rolebinding -n ${PROFILE_NAMESPACE} namespaceAdmin 
# delete serviceaccount
kubectl delete serviceaccount -n ${PROFILE_NAMESPACE} default-editor
# # delete  authorization policy
kubectl delete authorizationpolicy -n ${PROFILE_NAMESPACE} user-${PROFILE_NAMESPACE}-ardentmc-com-clusterrole-admin
# # delete namespace
kubectl delete namespace ${PROFILE_NAMESPACE}
# delete profile
kubectl delete profile ${PROFILE_NAMESPACE}

aws iam delete-role-policy --role-name ${PROFILE_NAMESPACE}-${CLUSTER_NAME}-role --policy-name kf-${PROFILE_NAMESPACE}-pipeline-s3
aws iam delete-role --role-name ${PROFILE_NAMESPACE}-${CLUSTER_NAME}-role