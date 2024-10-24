# README

To add a user, first add them via AWS Cognito. The user should be the first part of their email address, for example,

email: test.user@ardentmc.com
username: test.user

email: tuser@mission1st.pr
username: tuser

Add the user's email to the user, and use the provided initial password and this step is complete.

For a mission1st user, fill in the appropriate fields in the `./add-user/user_setup_mission1st.sh` and execute the file

Do the same for an ardentmc user with the `./add-user/user_setup_ardentmc.sh` file.

If fields are defined incorrectly, you may need to delete the user data. `./add-user/delete_user.sh` contains helpful commands that should remove many, but not all problematic configurations.


For additional information, refer to the Kubeflow (Profile Resources)[https://www.kubeflow.org/docs/components/central-dash/profiles/#profile-resources] documentation for the rationale behind user profile resource creation.