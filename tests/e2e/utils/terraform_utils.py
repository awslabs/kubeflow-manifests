import subprocess
import os

from e2e.utils.config import configure_resource_fixture


def create_test_tfvars_file(
    input_variables, tf_folder, filename="test-generated.auto.tfvars"
):
    file_path = os.path.join(tf_folder, filename)
    if os.path.exists(file_path):
        raise Exception(
            f"make delete failed in a previous installation. successfully delete the resources and delete {file_path}"
        )

    with open(file_path, "w") as file:
        for k, v in input_variables.items():
            file.write(f'{k}="{v}"\n')


def delete_test_tfvars_file(tf_folder, filename="test-generated.auto.tfvars"):
    file_path = os.path.join(tf_folder, filename)
    os.remove(file_path)


def terraform_installation(
    input_variables, tf_folder, installation_name, metadata, request
):

    initial_dir = os.getcwd()

    def on_create():
        create_test_tfvars_file(input_variables, tf_folder)

        os.chdir(tf_folder)
        retcode = subprocess.call("make deploy".split())
        os.chdir(initial_dir)
        assert retcode == 0

    def on_delete():
        os.chdir(initial_dir)
        os.chdir(tf_folder)
        retcode = subprocess.call("make delete".split())
        os.chdir(initial_dir)
        if retcode == 0:
            # keep tfvars file to retry delete manually
            delete_test_tfvars_file(tf_folder)
        assert retcode == 0

    return configure_resource_fixture(
        metadata_key=installation_name,
        resource_details=input_variables,
        on_create=on_create,
        on_delete=on_delete,
        metadata=metadata,
        request=request,
    )


def get_stack_output(output_name, tf_folder):
    initial_dir = os.getcwd()
    os.chdir(tf_folder)
    output = subprocess.check_output(
        f"terraform output -raw {output_name}".split()
    ).decode()
    os.chdir(initial_dir)

    return output

