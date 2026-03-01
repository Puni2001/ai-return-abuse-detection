"""
Script to deploy training job to Amazon SageMaker
"""

import boto3
import sagemaker
from sagemaker.xgboost import XGBoost
from datetime import datetime

# Initialize SageMaker session
sagemaker_session = sagemaker.Session()
role = sagemaker.get_execution_role()
region = boto3.Session().region_name

# S3 paths
bucket = f'return-abuse-data-lake-{boto3.client("sts").get_caller_identity()["Account"]}'
prefix = 'sagemaker-training'

s3_input_train = f's3://{bucket}/{prefix}/data/training_data.csv'
s3_output_path = f's3://{bucket}/{prefix}/output'

print(f"Training data: {s3_input_train}")
print(f"Output path: {s3_output_path}")

# Define XGBoost estimator
xgb_estimator = XGBoost(
    entry_point='train.py',
    source_dir='.',
    role=role,
    instance_count=1,
    instance_type='ml.m5.xlarge',
    framework_version='1.7-1',
    py_version='py3',
    output_path=s3_output_path,
    sagemaker_session=sagemaker_session,
    hyperparameters={
        'max_depth': 6,
        'learning_rate': 0.1,
        'n_estimators': 100,
        'min_child_weight': 1,
        'gamma': 0,
        'subsample': 0.8,
        'colsample_bytree': 0.8
    },
    tags=[
        {'Key': 'Project', 'Value': 'ReturnAbuseDetection'},
        {'Key': 'Environment', 'Value': 'prod'},
        {'Key': 'Team', 'Value': 'Soul'}
    ]
)

# Start training
print("\n🚀 Starting SageMaker training job...")
xgb_estimator.fit({'train': s3_input_train})

print("\n✅ Training job completed!")
print(f"Model artifacts: {xgb_estimator.model_data}")

# Deploy model to endpoint (optional)
deploy = input("\nDeploy model to endpoint? (y/n): ")
if deploy.lower() == 'y':
    print("\n🚀 Deploying model to endpoint...")
    predictor = xgb_estimator.deploy(
        initial_instance_count=1,
        instance_type='ml.t2.medium',
        endpoint_name=f'return-abuse-endpoint-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
    )
    print(f"\n✅ Model deployed to endpoint: {predictor.endpoint_name}")
