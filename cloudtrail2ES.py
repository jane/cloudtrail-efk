import json
import gzip
import requests
import boto3
import os
import tempfile

# set these env vars

# elasticsearch
es_user = os.environ.get('ES_USER')
# asdf
es_pass = os.environ.get('ES_PASS')
# foo.example.com:9200
host = os.environ.get('ES_HOST')
# cloudtrail
indexname = os.environ.get('ES_INDEX')
if indexname is None:
    indexname = "cloudtrail"

# constants
method = 'POST'
content_type = 'application/json'

# adjust as needed
filtered_sources = [
    "athena",
    "dynamodb",
    "glue",
    "sns"
]

s3 = boto3.client('s3')


# set the lambda handler to this_file.this_function
def lambda_handler(event, context):
    # attribute bucket and file name/path to variables
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']

    # just in case
    if (bucket is None or key is None):
        return

    s3obj = tempfile.NamedTemporaryFile(mode='w+b', delete=False)
    s3.download_fileobj(bucket, key, s3obj)
    s3obj.close()
    gzfile = gzip.open(s3obj.name, "r")
    response = json.loads(gzfile.readlines()[0])

    # in case something non-cloudtrail ends up in this bucket
    if ("Records" not in response):
        return

    eventcount = 1
    for i in response["Records"]:
        # filter out events by name here. example:
        # if (i["eventName"] in "GetQueryResultsStream"):
        #   continue

        # remove useless field
        i.pop('apiVersion', None)

        i["@timestamp"] = i["eventTime"]

        # example: lambda.aws.amazon.com -> lambda
        i["eventSource"] = i["eventSource"].split(".")[0]

        # filter out events by source here.
        if (i["eventSource"] in filtered_sources):
            continue

        data = json.dumps(i).encode('utf-8')

        # use eventTime for index
        event_date = i["eventTime"].split("T")[0]

        canonical_uri = '/' + indexname + '-' + event_date + '/_doc'
        url = 'https://' + host + canonical_uri

        headers = {'Content-Type': content_type}

        req = requests.post(
            url, data=data, headers=headers, auth=(es_user, es_pass))

        # could fail if we have a lot of data; retry
        retry_counter = 1

        while (req.status_code != 201) and (retry_counter < 4):
            req = requests.post(
                url, data=data, headers=headers, auth=(es_user, es_pass))

            retry_counter += 1
        eventcount += 1

    s3obj.close()
    os.unlink(s3obj.name)
    print("{} events in {}".format(eventcount, s3obj.name))
