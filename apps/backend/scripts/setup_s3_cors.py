#!/usr/bin/env python3
"""Script to set up S3 bucket CORS configuration."""

import json
import sys
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings


def setup_cors():
    """Set up CORS configuration for S3 bucket."""
    settings = get_settings()
    
    if not settings.s3_enabled:
        print("S3 is not enabled in configuration.")
        return
    
    # CORS configuration
    cors_configuration = {
        'CORSRules': [
            {
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE', 'HEAD'],
                'AllowedOrigins': [
                    'http://localhost:4200',
                    'http://localhost:8000',
                    settings.frontend_url,
                ],
                'ExposeHeaders': [
                    'ETag',
                    'x-amz-server-side-encryption',
                    'x-amz-request-id',
                    'x-amz-id-2',
                ],
                'MaxAgeSeconds': 3000,
            }
        ]
    }
    
    # Create S3 client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_default_region,
        endpoint_url=settings.s3_endpoint_url,
    )
    
    try:
        # Set CORS configuration
        s3_client.put_bucket_cors(
            Bucket=settings.s3_bucket_name,
            CORSConfiguration=cors_configuration,
        )
        print(f"✅ CORS configuration set successfully for bucket: {settings.s3_bucket_name}")
        
        # Verify the configuration
        response = s3_client.get_bucket_cors(Bucket=settings.s3_bucket_name)
        print("\nCurrent CORS configuration:")
        print(json.dumps(response['CORSRules'], indent=2))
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchBucket':
            print(f"❌ Bucket '{settings.s3_bucket_name}' does not exist.")
            print("\nTo create the bucket, run:")
            print(f"  aws s3 mb s3://{settings.s3_bucket_name}")
        else:
            print(f"❌ Error setting CORS configuration: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def save_cors_config():
    """Save CORS configuration to a JSON file for reference."""
    settings = get_settings()
    
    cors_config = [
        {
            "AllowedHeaders": ["*"],
            "AllowedMethods": ["GET", "PUT", "POST", "DELETE", "HEAD"],
            "AllowedOrigins": [
                "http://localhost:4200",
                "http://localhost:8000",
                settings.frontend_url,
            ],
            "ExposeHeaders": [
                "ETag",
                "x-amz-server-side-encryption",
                "x-amz-request-id",
                "x-amz-id-2",
            ],
            "MaxAgeSeconds": 3000,
        }
    ]
    
    cors_file = Path(__file__).parent / "s3_cors.json"
    with open(cors_file, "w") as f:
        json.dump(cors_config, f, indent=2)
    
    print(f"\n📄 CORS configuration saved to: {cors_file}")
    print("\nTo apply this configuration manually:")
    print(f"  aws s3api put-bucket-cors --bucket {settings.s3_bucket_name} --cors-configuration file://{cors_file}")


if __name__ == "__main__":
    print("🚀 Setting up S3 CORS configuration...\n")
    setup_cors()
    save_cors_config()