cat <<EOF > rolebinding-namespace-account-editor.yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: default-editor
  namespace: ${PROFILE_NAMESPACE}
  annotations:
    role: edit
    user: ${PROFILE_USER}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: kubeflow-edit
subjects:
- kind: ServiceAccount
  name: default-editor
  namespace: ${PROFILE_NAMESPACE}
EOF

kubectl create -f rolebinding-namespace-account-editor.yaml