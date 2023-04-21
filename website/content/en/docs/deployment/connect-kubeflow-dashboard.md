+++
title = "Connect to your Kubeflow Dashboard"
description = "Start experimenting and running your end-to-end ML workflows with Kubeflow on AWS"
weight = 70
+++

## Port-forward (Manifest deployment)
> Note: Make sure you are in the the root of the repository before running the following commands. Running pwd command should output `<path/to/kubeflow-manifests>` directory.

### Option 1: Amazon EC2 

Run the following command on your EC2 instance: 
```sh
make port-forward
```

Then, on your local machine, run the following:

```sh
ssh -i <path-to-your-key-pem> -L 8080:localhost:8080 -N ubuntu@ec2-<Public-IPv4-DNS>.compute-1.amazonaws.com -o ExitOnForwardFailure=yes
```

You can then open the browser and go to [http://localhost:8080/](http://localhost:8080/).

### Option 2: Docker 

Run the following command:
```sh
make port-forward IP_ADDRESS=0.0.0.0
```

You can then open the browser and go to [http://localhost:8080/](http://localhost:8080/).

### Option 3: AWS Cloud9

Connect to your Kubeflow dashboard with a single command:
```sh
make port-forward
```

Then, open the AWS Cloud9 browser and go to [http://localhost:8080/](http://localhost:8080/).

## Port-forward (Terraform deployment)
> Note: Make sure you are in the the root of the repository before running the following commands. Running pwd command should output `<path/to/kubeflow-manifests>` directory.
1. Update the `kubeconfig`:
    ```sh
    $(terraform output -raw configure_kubectl)
    ```

2. [Choose your port forward option](#port-forward-manifest-deployment)

## Open the browser

You can then open the browser and go to [http://localhost:8080/](http://localhost:8080/).

## Log into the Kubeflow UI

Use the following default credentials to log into the Kubeflow UI:
> Note: If you changed the default password using the steps in [Change the default user password]({{< ref "#change-the-default-user-password-kustomize" >}}), then use the password that you created.
- email : user@example.com
- password : 12341234

Congratulations! 🎉 Your Kubeflow on AWS setup is complete  

## Exposing Kubeflow over Load Balancer (Optional) 

In order to expose Kubeflow over an external address, you can set up AWS Application Load Balancer. Please take a look at the [Load Balancer guide]({{< ref "/docs/add-ons/load-balancer/guide.md" >}}) to set it up.

## Change the default user password (Kustomize)

For security reasons, we do not recommend using the default password for the default Kubeflow user when installing in security-sensitive environments. 

Define your own password before deploying. To define a password for the default user:

1. Pick a password for the default user, with email `user@example.com`, and hash it using `bcrypt`:

    ```sh
    python3 -c 'from passlib.hash import bcrypt; import getpass; print(bcrypt.using(rounds=12, ident="2y").hash(getpass.getpass()))'
    ```

2. Edit `upstream/common/dex/base/config-map.yaml` and fill the relevant field with the hash of the password you chose:

    ```yaml
    ...
      staticPasswords:
      - email: user@example.com
        hash: <enter the generated hash here>
    ```
