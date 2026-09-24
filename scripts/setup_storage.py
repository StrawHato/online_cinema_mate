"""Create the configured S3 bucket and allow public reads for stored media."""

import json
import os
import time

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError


def main() -> None:
    endpoint = f"http://{os.environ['S3_HOST']}:{os.environ['S3_PORT']}"
    bucket = os.environ["S3_BUCKET_NAME"]
    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=os.environ["S3_ACCESS_KEY"],
        aws_secret_access_key=os.environ["S3_SECRET_KEY"],
        region_name="us-east-1",
        config=Config(s3={"addressing_style": "path"}),
    )

    print(f"Waiting for S3 storage at {endpoint}...", flush=True)
    for attempt in range(60):
        try:
            client.list_buckets()
            break
        except (BotoCoreError, ClientError) as exc:
            if isinstance(exc, ClientError):
                status = exc.response.get("ResponseMetadata", {}).get(
                    "HTTPStatusCode", 0
                )
                if status < 500:
                    raise
            if attempt == 59:
                raise
            print(f"Storage is not ready ({exc}); retrying in 2 seconds...", flush=True)
            time.sleep(2)

    try:
        client.head_bucket(Bucket=bucket)
        print(f"Bucket '{bucket}' already exists.", flush=True)
    except ClientError as exc:
        status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
        code = exc.response.get("Error", {}).get("Code")
        if status != 404 and code not in {"404", "NoSuchBucket", "NotFound"}:
            raise
        client.create_bucket(Bucket=bucket)
        print(f"Created bucket '{bucket}'.", flush=True)

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": "*",
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{bucket}/*"],
            }
        ],
    }
    client.put_bucket_policy(Bucket=bucket, Policy=json.dumps(policy))
    print(f"Public read policy applied to '{bucket}'.", flush=True)


if __name__ == "__main__":
    main()
