import requests
import time


def test_url_is_up(subdomain_name):
    kubeflow_endpoint = "https://kubeflow." + subdomain_name
    print("kubeflow_endpoint:")
    print(kubeflow_endpoint)
    # wait a bit till website is accessible
    print("Wait for 60s for website to be available...")
    time.sleep(60)
    response = requests.get(kubeflow_endpoint)
    assert response.status_code == 200
    # request was redirected
    assert len(response.history) > 0
    # redirection was to cognito domain
    assert "auth." + subdomain_name in response.url


# Kubeflow sdk client need cookies provided by ALB. Currently it is not possible to programmatically fetch these cookies using tokens provided by cognito
# See - https://stackoverflow.com/questions/62572327/how-to-pass-cookies-when-calling-authentication-enabled-aws-application-loadbala
# The other way to test multiuser kfp is by using selenium and creating a session using a real browser. There are drivers which can be used via Selenium webdriver to programmatically control a browser
# e.g. https://chromedriver.chromium.org/getting-started
# This is a hack and has been implemented in this PR - https://github.com/kubeflow/pipelines/pull/4182
# TODO: explore if this will work in codebuild since there is an option to run headless i.e. without GUI
