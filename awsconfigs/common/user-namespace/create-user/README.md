# README

To add a user, first add them via AWS Cognito. The user should be the first part of their email address, for example,

email: test.user@ardentmc.com
username: test.user

email: test.user@mission1st.pr
username: test.user

Be sure to add the user's email to the Cognito user identity and use the provided initial password and this step is complete.

## Missions1t Users

For a mission1st user, fill in the appropriate fields in the `./create-user/create_user_mission1st.sh` and execute the file

## ArdentMC Users

Do the same for an ardentmc user with the `./create-user/user_setup_ardentmc.sh` file.

# Default user creation

The default user profile will be managed by the kfp-pipeline-controller. It automates the creation and deletion of resources, such as the user's namespace, service accounts, and pod deployments that add functionality to kubeflow's pipelines. Each user should have two deployments, ml-pipeline-ui-artifact and ml-pipeline-visualizationserver. Without these deployments, kubeflow pipelines will not be visualized via the central dashboard.

## User creation without KF Pipelines

Another method of creating a user profile and namespace that is not centrally managed by the kfp-pipelines-controller can be achieved using the `/profile_namespace_creation/create_profile_no_kfp_pipeline.sh` method. This method will provide a detached experience where users still have the ability to create kubeflow notebooks, persistent volumes, and access kubeflow's central dashboard with their own username. They will not have the ability to use the full functionality of the Pipelines UI, so pipeline graphs will not load and neither will any helpful pipeline metadata. A correctly formatted pipeline yaml can still be uploaded and run, but the user will be on their own when trying to observe the results of the run and any artifacts they intend to produce. Correctly formatted pipelines can still run and store objects in minio and S3. These artifacts can be discovered by observing the pod logs via the `kubectl -n <user-namespace> logs <pod-name>` command.

### Additional Note

Once a profile and namespace are created without kfp-pipeline-controller administration, there does not appear to be a way to grant the controller access to convert the profile into a controlled profile without losing all of the user's data. The user's namespace must be deleted to grant control to the pipeline controller.

## Troubleshooting

If fields are defined incorrectly, you may need to delete the user data. `./create-user/delete_user.sh` contains helpful commands that should remove many, but not all problematic configurations.

If the profile was set up to default way, it is controlled by the kfp-pipelines-controller. This means that **if the user's profile is deleted, the profile controller will delete ALL resources connected to that user**, including notebooks, persistent volumes, deployments, etc.

### Documentation on Profiles without Pipelines UI Functionality

For additional information on manually created user profiles, refer to the Kubeflow (Profile Resources)[https://www.kubeflow.org/docs/components/central-dash/profiles/#profile-resources] documentation for the rationale behind user profile resource creation.