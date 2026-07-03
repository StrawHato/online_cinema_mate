#!/bin/sh

set -e

echo "Waiting for MinIO to become available..."

until mc alias set minio \
    "http://$S3_HOST:$S3_PORT" \
    "$S3_ACCESS_KEY" \
    "$S3_SECRET_KEY" >/dev/null 2>&1
do
    echo "MinIO is not ready yet. Retrying in 2 seconds..."
    sleep 2
done

echo "MinIO is ready."

if mc stat "minio/$S3_BUCKET_NAME" >/dev/null 2>&1; then
    echo "Bucket '$S3_BUCKET_NAME' already exists."
else
    echo "Creating bucket '$S3_BUCKET_NAME'..."
    mc mb "minio/$S3_BUCKET_NAME"
fi

echo "Setting public read policy..."
mc anonymous set download "minio/$S3_BUCKET_NAME"

echo "Bucket policy:"
mc anonymous get "minio/$S3_BUCKET_NAME"

echo "MinIO setup completed successfully."
