import boto3
import json
import uuid
from decimal import Decimal
from urllib.parse import unquote_plus
import os


rekognition = boto3.client('rekognition')
ddb = boto3.resource('dynamodb')
dynamodb_table = os.environ['DYNAMODB_TABLE']


# --------------- Functions to call Rekognition APIs ------------------

def get_celeb(bucket, key):
    response = rekognition.recognize_celebrities(Image={"S3Object": {"Bucket": bucket, "Name": key}})
    return response

# --------------- Main handler ------------------


def lambda_handler(event, context):
    
    # DynamoDB table
    table = ddb.Table(dynamodb_table)
    
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])



        # Calls rekognition celebrity API to detect faces in S3 object
        print("Calling rekognition service")

        face_detect = get_celeb(bucket, key)
        faces_map = json.loads(json.dumps(face_detect), parse_float=Decimal)
        
        
        new_item = {
            'Id': str(uuid.uuid4()),
            'faceData':faces_map,
            }
        
        try:
            print("Creating Table entry")

            # PUT metadata to DynamoDB table
            table.put_item(Item=new_item)
        except Exception as e:
            return e
        return True