export NAMESPACE=ai-validator
export PROFILE_USER=test.user@ardentmc.com
export ROLE=edit
export SAFE_USER_PROFILE_NAME=test-user-ardentmc-com

kubectl create namespace ${NAMESPACE}

cat <<EOF > rolebinding-user.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: user-${SAFE_USER_PROFILE_NAME}-clusterrole-${ROLE}
  namespace: ${NAMESPACE}
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

cat <<EOF > rolebinding-service-account-editor.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: default-editor
  namespace: ${NAMESPACE}
  annotations:
    role: edit
    user: ${PROFILE_USER}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: kubeflow-edit
subjects:
  - apiGroup: rbac.authorization.k8s.io
    kind: User
    name: ${PROFILE_USER}
EOF

kubectl create -f rolebinding-service-account-editor.yaml
kubectl -n ${NAMESPACE} create serviceaccount default-editor

cat << EOF > authorizationpolicy.yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: user-${SAFE_USER_PROFILE_NAME}-clusterrole-${ROLE}
  namespace: ${NAMESPACE}
  annotations:
    role: ${ROLE}
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