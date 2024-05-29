aws iam create-role --role-name jhoward-kf-role --assume-role-policy-document file://trust.json

aws iam attach-role-policy --role-name jhoward-kf-role --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
