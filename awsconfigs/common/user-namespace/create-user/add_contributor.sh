# user first name
export FIRSTNAME=daniel
# user last name
export LASTNAME=desouza
# name of the profile to grant the contributor edit access to
export PROFILE_NAME=ai-validator
# kubeflow only permits edit access for contributors for now
export ROLE=edit
# email of the contributor
export RAW_USER_EMAIL=${FIRSTNAME}.${LASTNAME}@ardentmc.com
# contributor email replaced with safe character "-"
export CONTRIBUTOR_SAFE_USER_PROFILE_NAME=${FIRSTNAME}-${LASTNAME}-ardentmc-com

# create a rolebinding for the new contributor
cat <<EOF > contributor-rolebinding.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: user-${CONTRIBUTOR_SAFE_USER_PROFILE_NAME}-clusterrole-${ROLE}
  namespace: ${PROFILE_NAME}
  annotations:
    role: ${ROLE}
    user: ${RAW_USER_EMAIL}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: kubeflow-${ROLE}
subjects:
  - apiGroup: rbac.authorization.k8s.io
    kind: User
    name: ${RAW_USER_EMAIL}
EOF

# create authorization policy
cat <<EOF > contributor-authorization-policy.yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: user-${CONTRIBUTOR_SAFE_USER_PROFILE_NAME}-clusterrole-${ROLE}
  namespace: ${PROFILE_NAME}
  annotations:
    role: ${ROLE}
    user: ${RAW_USER_EMAIL}
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
            - ${RAW_USER_EMAIL}
EOF

kubectl create -f contributor-rolebinding.yaml
kubectl create -f contributor-authorization-policy.yaml
