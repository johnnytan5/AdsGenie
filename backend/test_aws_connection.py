#!/usr/bin/env python3
"""
Test script to verify AWS S3 and DynamoDB connections.
Run this after setting up your AWS resources.
"""
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.core.s3 import get_s3_client
from app.core.dynamodb import get_projects_table

def test_s3():
    """Test S3 connection and bucket access."""
    print("Testing S3 connection...")
    try:
        client = get_s3_client()
        
        # List buckets
        response = client.list_buckets()
        bucket_names = [b['Name'] for b in response['Buckets']]
        print(f"✅ S3 connection successful!")
        print(f"   Available buckets: {bucket_names}")
        
        # Check if our bucket exists
        if settings.S3_BUCKET_NAME in bucket_names:
            print(f"✅ Bucket '{settings.S3_BUCKET_NAME}' found!")
            
            # Try to list objects in the bucket
            try:
                response = client.list_objects_v2(Bucket=settings.S3_BUCKET_NAME, MaxKeys=5)
                object_count = response.get('KeyCount', 0)
                print(f"   Bucket contains {object_count} objects (showing first 5)")
            except Exception as e:
                print(f"   ⚠️  Could not list objects: {e}")
        else:
            print(f"❌ Bucket '{settings.S3_BUCKET_NAME}' not found!")
            print(f"   Please create the bucket in region '{settings.AWS_REGION}'")
            return False
            
        return True
    except Exception as e:
        print(f"❌ S3 connection failed: {e}")
        return False

def test_dynamodb():
    """Test DynamoDB connection and table access."""
    print("\nTesting DynamoDB connection...")
    try:
        table = get_projects_table()
        
        # Check table status
        table.load()
        print(f"✅ DynamoDB connection successful!")
        print(f"   Table name: {table.table_name}")
        print(f"   Table status: {table.table_status}")
        print(f"   Table ARN: {table.table_arn}")
        
        # Try to scan (get count)
        try:
            response = table.scan(Select='COUNT')
            item_count = response.get('Count', 0)
            print(f"   Table contains {item_count} items")
        except Exception as e:
            print(f"   ⚠️  Could not scan table: {e}")
            
        return True
    except Exception as e:
        print(f"❌ DynamoDB connection failed: {e}")
        print(f"   Make sure table '{settings.DYNAMODB_TABLE_NAME}' exists in region '{settings.AWS_REGION}'")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("AWS Connection Test")
    print("=" * 60)
    print(f"Region: {settings.AWS_REGION}")
    print(f"S3 Bucket: {settings.S3_BUCKET_NAME}")
    print(f"DynamoDB Table: {settings.DYNAMODB_TABLE_NAME}")
    print("=" * 60)
    
    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        print("❌ AWS credentials not configured!")
        print("   Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in your .env file")
        return
    
    s3_ok = test_s3()
    dynamodb_ok = test_dynamodb()
    
    print("\n" + "=" * 60)
    if s3_ok and dynamodb_ok:
        print("✅ All tests passed! Your AWS setup is ready.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    print("=" * 60)

if __name__ == "__main__":
    main()
