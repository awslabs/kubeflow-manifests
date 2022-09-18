variable "aws_access_key" {
  type        = string
  description = "AWS access key to authenticate minio client"
}

variable "aws_secret_key" {
  type        = string
  description = "AWS secret key to authenticate minio client"
}

variable "secret_recovery_window_in_days" {
  type = number
  default = 7
}

variable "force_destroy_bucket" {
  type = bool
  description = "Destroys s3 bucket even when the bucket is not empty"
  default = false
}