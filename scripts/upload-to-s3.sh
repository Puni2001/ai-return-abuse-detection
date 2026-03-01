#!/bin/bash

# Upload sample data to AWS S3
# Run this after: aws configure

BUCKET_NAME="return-abuse-data-lake-punith"
REGION="ap-south-1"

echo "Creating S3 bucket..."
aws s3 mb s3://${BUCKET_NAME} --region ${REGION}

echo "Uploading files to S3..."
aws s3 cp sample-data/customers.csv s3://${BUCKET_NAME}/raw/customers/customers.csv
aws s3 cp sample-data/products.csv s3://${BUCKET_NAME}/raw/products/products.csv
aws s3 cp sample-data/orders.csv s3://${BUCKET_NAME}/raw/orders/orders.csv
aws s3 cp sample-data/returns.csv s3://${BUCKET_NAME}/raw/returns/returns.csv

echo "Verifying upload..."
aws s3 ls s3://${BUCKET_NAME}/raw/ --recursive

echo "✓ Done! Files uploaded to S3"
echo "Bucket: s3://${BUCKET_NAME}"
