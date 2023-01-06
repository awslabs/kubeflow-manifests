CONFIG_FILE = "./tools/helmify/src/config.yaml"
KUSTOMIZED_BUILD_OUTPUT_PATH = (
    "./tools/helmify/generated_output/kustomized_output_files"
)
HELM_TEMP_OUTPUT_PATH = "./tools/helmify/generated_output/helm_chart_temp_output_files"
POSSIBLE_DEPLOYMENT_OPTIONS = [
    "vanilla",
    "cognito",
    "rds-s3",
    "rds-only",
    "s3-only",
    "katib-external-db-with-kubeflow",
]
POSSIBLE_PROBLEM_FILE_TYPES = ["ConfigMap", "ClusterServingRuntime"]
