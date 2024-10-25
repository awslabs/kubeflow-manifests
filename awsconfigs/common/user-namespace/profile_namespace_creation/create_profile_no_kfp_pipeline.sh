# 
# This script creates a profile that is NOT managed by the 
# kfp-pipeline-profile-controller. KFP pipelines will not function
# as expected, but Notebooks can be created.
# Depends on running create-user/user_setup.sh, where variables are defined.

kubectl create namespace ${PROFILE_NAMESPACE}

cat <<EOF > rolebinding-user.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: namespaceAdmin
  namespace: ${PROFILE_NAMESPACE}
  annotations:
    role: ${ROLE}
    user: ${PROFILE_USER}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: kubeflow-${ROLE}
subjects:
  - apiGroup: rbac.authorization.k8s.io
    kind: User
    name: ${PROFILE_USER}
EOF

kubectl create -f rolebinding-user.yaml
# kubectl apply -f rolebinding-user.yaml

cat <<EOF > rolebinding-service-account-editor.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: default-editor
  namespace: ${PROFILE_NAMESPACE}
  annotations:
    role: edit
    user: ${PROFILE_USER}
    eks.amazonaws.com/role-arn: arn:aws:iam::905418165254:role/${PROFILE_NAMESPACE}-kf-role
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: kubeflow-edit
subjects:
  - apiGroup: rbac.authorization.k8s.io
    kind: User
    name: ${PROFILE_USER}
EOF

kubectl -n ${PROFILE_NAMESPACE} create serviceaccount default-editor
# kubectl -n ${PROFILE_NAMESPACE} apply serviceaccount default-editor

cat << EOF > authorizationpolicy.yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: user-${SAFE_USER_PROFILE_NAME}-clusterrole-admin
  namespace: ${PROFILE_NAMESPACE}
  annotations:
    role: admin
    user: ${PROFILE_USER}
spec:
  rules:
    - from:
        - source:
            ## for more information see the KFAM code:
            ## https://github.com/kubeflow/kubeflow/blob/v1.8.0/components/access-management/kfam/bindings.go#L79-L110
            principals:
              ## required for kubeflow notebooks
              ## TEMPLATE: "cluster.local/ns/<ISTIO_GATEWAY_NAMESPACE>/sa/<ISTIO_GATEWAY_SERVICE_ACCOUNT>"
              - "cluster.local/ns/istio-system/sa/istio-ingressgateway-service-account"

              ## required for kubeflow pipelines
              ## TEMPLATE: "cluster.local/ns/<KUBEFLOW_NAMESPACE>/sa/<KFP_UI_SERVICE_ACCOUNT>"
              - "cluster.local/ns/kubeflow/sa/ml-pipeline-ui"
      when:
        - key: request.headers[kubeflow-userid]
          values:
            - ${PROFILE_USER}
EOF

kubectl create -f authorizationpolicy.yaml
# kubectl apply -f authorizationpolicy.yaml