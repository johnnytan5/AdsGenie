# AWS Setup Guide - S3 Bucket and DynamoDB Table

This guide will help you create the required AWS resources for AdsGenie backend.

## Prerequisites

- AWS Account with appropriate permissions
- AWS CLI installed and configured (optional, but helpful)
- Your AWS credentials configured in `.env` file

---

## 1. Create S3 Bucket

### Option A: Using AWS Console (Web UI)

1. **Sign in to AWS Console**
   - Go to https://console.aws.amazon.com/
   - Sign in with your AWS account

2. **Navigate to S3**
   - Search for "S3" in the top search bar
   - Click on "S3" service

3. **Create Bucket**
   - Click "Create bucket" button
   - **Bucket name**: `adsgenie-assets` (or your preferred name)
   - **AWS Region**: `ap-southeast-1` (Asia Pacific - Singapore)
   - **Object Ownership**: ACLs disabled (recommended)
   - **Block Public Access settings**: 
     - ✅ Block all public access (keep checked for security)
     - Note: Your app will access files via IAM credentials
   
4. **Bucket Versioning**: Disable (unless you need versioning)

5. **Default encryption**: Enable (recommended)
   - Encryption type: Amazon S3 managed keys (SSE-S3)

6. **Click "Create bucket"**

### Option B: Using AWS CLI

```bash
# Create bucket
aws s3 mb s3://adsgenie-assets --region ap-southeast-1

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket adsgenie-assets \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

---

## 2. Create DynamoDB Table

### Option A: Using AWS Console (Web UI)

1. **Navigate to DynamoDB**
   - Search for "DynamoDB" in AWS Console
   - Click on "DynamoDB" service

2. **Create Table**
   - Click "Create table" button
   - **Table name**: `Projects`
   - **Partition key**: 
     - Key name: `project_id`
     - Key type: `String`
   - **Table settings**: 
     - Use default settings (On-demand capacity mode recommended for hackathons)
     - Or choose Provisioned capacity if you prefer:
       - Read capacity: 5 units
       - Write capacity: 5 units

3. **Additional Settings** (optional):
   - **Encryption**: Enable encryption at rest (recommended)
   - **Tags**: Add tags if needed (e.g., `Project: AdsGenie`)

4. **Click "Create table"**

5. **Wait for table to be created** (usually takes a few seconds)

### Option B: Using AWS CLI

```bash
aws dynamodb create-table \
  --table-name Projects \
  --attribute-definitions AttributeName=project_id,AttributeType=S \
  --key-schema AttributeName=project_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region ap-southeast-1
```

---

## 3. Verify IAM Permissions

Make sure your IAM user has the following permissions:

### Quick Setup (Recommended for Hackathons):
Attach these AWS managed policies to your IAM user:
- `AmazonS3FullAccess`
- `AmazonDynamoDBFullAccess`

### Custom Policies (More Secure):

**S3 Permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::adsgenie-assets",
        "arn:aws:s3:::adsgenie-assets/*"
      ]
    }
  ]
}
```

**DynamoDB Permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Scan",
        "dynamodb:Query"
      ],
      "Resource": "arn:aws:dynamodb:ap-southeast-1:*:table/Projects"
    }
  ]
}
```

---

## 4. Update Your .env File

Make sure your `.env` file in the backend directory has:

```env
AWS_REGION=ap-southeast-1
AWS_ACCESS_KEY_ID=your-actual-access-key-id
AWS_SECRET_ACCESS_KEY=your-actual-secret-access-key
S3_BUCKET_NAME=adsgenie-assets
DYNAMODB_TABLE_NAME=Projects
```

---

## 5. Test the Setup

### Test S3 Connection:
```python
# Run this in Python shell
from app.core.s3 import get_s3_client

client = get_s3_client()
response = client.list_buckets()
print("S3 Buckets:", [b['Name'] for b in response['Buckets']])
```

### Test DynamoDB Connection:
```python
# Run this in Python shell
from app.core.dynamodb import get_projects_table

table = get_projects_table()
print("Table name:", table.table_name)
print("Table status:", table.table_status)
```

### Or test via API:
1. Start your backend: `uvicorn app.main:app --reload`
2. Create a test project: `POST http://localhost:8000/api/v1/projects`
   ```json
   {
     "name": "Test Project",
     "aspect_ratio": "16:9"
   }
   ```
3. Check DynamoDB console to see if the item was created

---

## 6. Troubleshooting

### S3 Issues:
- **403 Forbidden**: Check IAM permissions
- **Bucket not found**: Verify bucket name and region match your config
- **Access Denied**: Ensure your AWS credentials have S3 permissions

### DynamoDB Issues:
- **ResourceNotFoundException**: Table doesn't exist or wrong region
- **AccessDeniedException**: Check IAM permissions
- **ValidationException**: Check table name matches config

### Common Issues:
- **Wrong Region**: Make sure all resources are in `ap-southeast-1`
- **Credentials**: Verify AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are correct
- **Permissions**: Ensure IAM user has necessary permissions

---

## 7. Cost Considerations (for Hackathons)

### S3:
- **Free Tier**: 5 GB storage, 20,000 GET requests, 2,000 PUT requests per month
- **Storage**: ~$0.023 per GB/month (after free tier)
- **Requests**: $0.005 per 1,000 PUT requests, $0.0004 per 1,000 GET requests

### DynamoDB:
- **Free Tier**: 25 GB storage, 200 million read/write request units per month
- **On-demand mode**: $1.25 per million write units, $0.25 per million read units

**For a hackathon, you'll likely stay within free tier limits!**

---

## Quick Checklist

- [ ] S3 bucket `adsgenie-assets` created in `ap-southeast-1`
- [ ] S3 bucket encryption enabled
- [ ] DynamoDB table `Projects` created with partition key `project_id`
- [ ] IAM user has S3 and DynamoDB permissions
- [ ] `.env` file configured with correct credentials
- [ ] Tested connection to both services
