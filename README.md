# cloudtrail-logs-to-AWS-Elasticsearch-Service

This will pull objects from S3 as they are delivered and will post them into your ElasticSearch cluster. It gets its privileges from an IAM role (see ). It gets all its configuration from Lambda environment variables. You should not need to edit the source code to deploy it.

Once you've got CloudTrail reliably inserted into your ElasticSearch cluster, start looking at stuff like [Traildash2](https://github.com/adcreare/traildash2) or AWS [cloudwatch logs subscription consumer](https://github.com/amazon-archives/cloudwatch-logs-subscription-consumer/tree/master/configuration/kibana). Both are very old, but they contain some useful widgets for visualisations.


![CloudTrail Sample Dashboard](https://assets.grumpy.world/uploads/cloudtrail-kibana.png)]

# Prerequisites

- Access to [AWS Lambda](https://console.aws.amazon.com/lambda/home)
- CloudTrail already set to store logs in an s3 bucket. Don't have that? Follow this [documentation](https://docs.aws.amazon.com/AmazonS3/latest/dev/cloudtrail-logging.html).
- An elasticsearch cluster. Either build it yourself, or [follow the tutorial in the documentation](https://docs.aws.amazon.com/elasticsearch-service/latest/developerguide/es-gsg-create-domain.html).

# Installation

Once you've got CloudTrail logging to S3 and your ElasticSearch cluster accepting input, you're ready to do this work. This will set up an S3 event listener. When an object is put in S3, this code gets called. This code unzips the S3 object and squirts it into ElasticSearch.

## Set Up IAM permissions
You need to create some policies and attach them to a role. That will give your Lambda function the ability to execute. The easiest way to do this is to create a single IAM policy that grants all the permissions you need, and then attach that one policy to the Lambda role. (You could have a few policies—one for elasticsearch, one for S3, one for CloudWatch Logs—and then attach 3 policies to the one role)

### IAM Policy

The IAM policy allows 3 things: Reading your S3 bucket to get cloudtrail, posting records to your ElasticSearch cluster, and CloudWatch Logs for writing any errors or logging.

1. Edit the `lambda-iam-policy.json` file
   1. Add in the bucket name for your bucket.
   2. Add in the domain name you assigned to your ElasticSearch domain.
1. Create an IAM policy, name it something like `CloudTrailESAccess` and set its contents to be the `lambda-iam-policy.json` file.

### Create a Role For your Lambda Function

Create an AWS IAM role.
1. Choose Lambda as the service for the role.
2. Attach the policy you created.

### Prep the Lambda Function

1. Clone this repo
1. On your terminal, install the requests module on the same folder with `pip install requests -t .`
1. Make a zip file that includes the python file and the requests library. From within the repo, run `zip -r lambda-function.zip cloudtrail2ES.py *`

### Create the Lambda Function

These are instructions for doing it by hand in the console. There's also a (cloudtrail2ES.yaml) file that contains some CloudFormation.

1. Create a new Lambda Function
2. Choose **Python 3.6** as a runtime.
3. Choose to start with an empty function.
4. Set the handler for the function is `lambda_handler`
5. Set the environment variables:
   * `ES_INDEX` set to something like `cloudtrail`. That will result in ElasticSearch indexes like `cloudtrail-2019-01-19`.
   * `ES_HOST` set to the name of your ElasticSearch endpoint. You can get that from the console or by running `aws es describe-elasticsearch-domain`. The value will look something like: `search-DOMAIN-abcdefgabcdefg.eu-west-1.es.amazonaws.com`. You don't want anything else (no 'https' or / or anything).
6. Test the Lambda function.
   1. Edit the `test-cloudtrail-event.json` file and change the bucket name to be your CloudTrail bucket. Go find a real key ("file name") of a CloudTrail object in your bucket and put that in the `key` parameter.
   1. Invoke the test and set your test event to be this JSON object. Debug any problems.
   1. If the test was successful, you have a few objects in your ElasticSearch cluster now. 
   1. If the test was unsuccessful, go into the CloudWatch Logs of your lambda function and look at the error messages. 

### Launch the Lambda from S3 Events

1. Go to your S3 Bucket in the console.
1. Click on Properties
1. Click on Events
1. Click **+ Add Notification**
1. Name the event
1. For **Events**, select "All object create events"
1. For **Prefix**, enter an appropriate prefix. Probably `AWSLogs/`
1. For **Send to**, select the lambda function you created
1. Click **Save**.

### Seeing it Work

It will take time. CloudTrail logs are delivered every few minutes. The S3 events fire pretty much immediately. Then the records are sent to ElasticSearch.

1. Click on the Kibana link in the ElasticSearch console.
1. Click on the Management gear icon
1. Click on **+ Create Index Pattern**
1. Name the index pattern `cloudtrail-*` (or whatever you used for the `ES_INDEX` value). You should see something helpful like **Your index pattern matches 2 indices**
1. Choose the `@timestamp` field for your timestamp
1. Save the index
1. Click on the **Discover** link at the top left. You should see some CloudTrail records.

### Lambda logs

On lambda web console, in the monitoring tab, theres a link for its logs on cloudwatch, you can see what the lambda function is doing.

# My changes

I updated it to run on Python 3.6 and to draw its configuration from the environment. It should not need to be modified code-wise. I also added a quick check in case the object isn't a CloudTrail record. I enable CloudTrail Digests on my logs, and those end up in somewhat similar paths.

# Acknowledgements

You might want to look at [Fernando's blog](https://www.fernandobattistella.com.br/log_processing/2016/03/13/Cloudtrail-S3-Lambda-Elasticsearch.html).

Thanks to [the original](https://github.com/argais/cloudtrail_aws_es.git) and to [pavan3401](https://github.com/pavan3401/cloudtrail-logs-to-AWS-Elasticsearch-Service) for forking and improving some.
