import boto3
import datetime
import xml.etree.ElementTree as ET


xml_path = "../canary/integration_tests.xml"

def readXML_and_publish_metrics_to_cw():
    tree = ET.parse(xml_path)
    root = tree.getroot
    failures = root.attrib['failures']
    errors = root.attrib['errors']
    tests = root.attrib['tests']
    timestamp = root.attrib['timestamp']

    success_rate = 1 - (failures/tests)

    print (f"Failures: {failures}")
    print (f"Errors: {errors}")
    print (f"Total tests: {tests}")
    print (f"Success_rate: {success_rate}")

    #push to cloudwatch
    # We can only push a max of 20 metrics at a time
        # Split metrics into chunks of 20 so that we have minimum number of put_metric_data calls
    cw_client = boto3.client("cloudwatch")
    # Define the metric data
    metric_data = [
        {
            'MetricName': 'failures',
            'Timestamp': timestamp,
            'Value': failures,
            'Unit': 'Count'
        },
        {
            'MetricName': 'errors',
            'Timestamp': timestamp,
            'Value': errors,
            'Unit': 'Count'
        },
        {
            'MetricName': 'total_tests',
            'Timestamp': timestamp,
            'Value': tests,
            'Unit': 'Count'
        },
        {
            'MetricName': 'successes_rate',
            'Timestamp': timestamp,
            'Value': success_rate,
            'Unit': 'Count'
        }
    ]

# Use the put_metric_data method to push the metric data to CloudWatch
    try:
        response = cw_client.put_metric_data(
            Namespace='Canary_Telemetry',
            MetricData=metric_data
        )
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print("Successfully pushed data to CloudWatch")
            # return 200 status code if successful
            return 200
        else:
            # raise exception if the status code is not 200
            raise Exception("Unexpected response status code: {}".format(response['ResponseMetadata']['HTTPStatusCode']))
    except Exception as e:
        print("Error pushing data to CloudWatch: {}".format(e))
        # raise exception if there was an error pushing data to CloudWatch
        raise

    



    

def main(): 
    readXML_and_publish_metrics_to_cw()

if __name__ == "__main__":
    main()


