terraform {
    backend "s3" {
        bucket = "tform-aivalidator"
        key    = "tfstate-backup"
        region = "us-east-1"
    }
}