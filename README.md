# cloudtrail_efk

Takes Cloudtrail logs from S3 and puts them in Elasticsearch.

## Setup:

### IAM

You need to create some policies and attach them to a role. That will give your
Lambda function the ability to execute. The easiest way to do this is to create
a single IAM policy that grants all the permissions you need, and then attach
that one policy to the Lambda role. (You could have a few policies—one for
elasticsearch, one for S3, one for CloudWatch Logs—and then attach 3 policies to
the one role)

The IAM policy allows 3 things: Reading your S3 bucket to get cloudtrail,
posting records to your ElasticSearch cluster, and CloudWatch Logs for writing
any errors or logging.

1. Edit the `lambda-iam-policy.json` file
   1. Add in the bucket name for your bucket.
   1. Add in the domain name you assigned to your ElasticSearch domain.
1. Create an IAM policy, name it like `cloudtrail_efk` and set its contents to
   be the `lambda-iam-policy.json` file.
1. Create an AWS IAM role.
1. Choose Lambda as the service for the role.
1. Attach the policy you created.
1. Attach `AWSLambdaVPCAccessExecutionRole` as well.

### Lambda

1. Pull this repo
1. `pip install requests -t .`
1. Make any changes you need
1. Tag appropriately (use semver)
1. `zip -r cloudtrail_efk.zip cloudtrail2ES.py *`
1. Create a new lambda in the AWS console with Python 3
1. Set the handler to be `cloudtrail2ES.lambda_handler`
1. Fill in your environment variables. Example below
1. Test the lambda function:
  * Edit `test-cloudtrail-event.json` to have the correct bucket and a real key
    (filename in S3)
  * Try the test and make sure your data is showing up in ES
1. Publish a Lambda version that matches your Git tag

Example environment variables:
```
ES_INDEX: cloudtrail
ES_HOST: foo.example.com:9200
ES_USER: cloudtrail_lambda
ES_PASS: very_good_password
```

### S3

1. Go to your S3 Bucket in the console.
1. Click on Properties
1. Click on Events
1. Click **+ Add Notification**
1. Name the event
1. For **Events**, select "All object create events"
1. For **Prefix**, enter an appropriate prefix. Probably `AWSLogs/`
1. For **Send to**, select the lambda function you created
1. Click **Save**.
