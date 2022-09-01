resources:
- ../../default
patches:
- path: role.json
  target:
    group: rbac.authorization.k8s.io
    version: v1
    kind: ClusterRole
    name: ack-sagemaker-controller
- path: role-binding.json
  target:
    group: rbac.authorization.k8s.io
    version: v1
    kind: ClusterRoleBinding
    name: ack-sagemaker-controller-rolebinding