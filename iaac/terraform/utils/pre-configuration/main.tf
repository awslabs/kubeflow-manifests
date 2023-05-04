data "http" "aws_efs_csi_driver_example_policy" {
  url = "https://raw.githubusercontent.com/kubernetes-sigs/aws-efs-csi-driver/v1.5.4/docs/iam-policy-example.json"
}

resource "aws_iam_policy" "aws_efs_csi_driver_policy" {
  name        = "efs-csi-driver-${var.cluster_name}"
  description = "Policy for the AWS EFS CSI driver service account"

  policy = data.http.aws_efs_csi_driver_example_policy.response_body
}