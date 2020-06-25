"""An AWS Python Pulumi program"""

import pulumi
from pulumi_aws import s3,lambda_,iam,dynamodb


# Create bucket that acts as a trigger for Lambda when an image is uploaded
celeb_img_bucket = s3.Bucket('celeb-imgIdentify-bucket')

# Create DynamoDB table
dynamo_table = dynamodb.Table(
    name="rekognition_entries", # If name is provided then Pulumi doesn't add the hex suffix for the created resource names
    resource_name="rekognition_entries",
    attributes=[
                {
                    "name": "Id",
                    "type": "S",
                },
            ],
    billing_mode="PAY_PER_REQUEST",
    hash_key="Id",

)

# Create Lambda IAM lambda_role
lambda_role = iam.Role(
    resource_name='lambda-ffmpeg-iam-role',
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "sts:AssumeRole",
                "Principal": {
                    "Service": "lambda.amazonaws.com"
                },
                "Effect": "Allow",
                "Sid": ""
            }
        ]
    }"""
)

lambda_role_policy = iam.RolePolicy(
    resource_name='lambda-ffmpeg-iam-policy',
    role=lambda_role.id,
    policy="""{
        "Version": "2012-10-17",
        "Statement": [
            {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents",
                "s3:*",
                "dynamodb:PutItem",
                "rekognition:*"
            ],
            "Resource": "*"
        }
        ]
    }"""
)

# Create Lambda function
lambda_rekognition = lambda_.Function(
    resource_name='celebrity_rekog',
    role=lambda_role.arn,
    runtime="python3.6",
    handler="celeb_rekognition.lambda_handler",
    code=pulumi.AssetArchive({
        '.': pulumi.FileArchive('./lambda_rekognition')
    }),
    timeout=15,
    memory_size=128,
    environment= { "variables":
     {"DYNAMODB_TABLE":
     "rekognition_entries"}
     }
)

# Give bucket permission to invoke Lambda
lambda_event = lambda_.Permission(
    resource_name="lambda_img_event",
    action="lambda:InvokeFunction",
    principal="s3.amazonaws.com",
    source_arn=celeb_img_bucket.arn,
    function=lambda_rekognition.arn
)

# Bucket notification that triggers Lambda on Put operation - For JPG
bucket_notification = s3.BucketNotification(
    resource_name="s3_notification",
    bucket=celeb_img_bucket.id,
    lambda_functions=[{
        "lambda_function_arn":lambda_rekognition.arn,
        "events": ["s3:ObjectCreated:*"],
        "filterSuffix":".jpg"
    }]
)




# Export created assets (buckets, lambda function, lambda layer)
pulumi.export('bucket', celeb_img_bucket.id)
pulumi.export('lambda function', lambda_rekognition.arn)
pulumi.export('dynamo table', dynamo_table.arn)
