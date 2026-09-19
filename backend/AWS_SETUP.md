# AWS Setup Guide — FloodRoute

## Prerequisites

- AWS account with appropriate permissions
- AWS CLI installed and configured
- Python 3.10+

## Step 1: Create S3 Bucket

```bash
aws s3api create-bucket \
  --bucket floodroute-reports \
  --region us-east-1
```

For regions other than us-east-1:
```bash
aws s3api create-bucket \
  --bucket floodroute-reports \
  --region us-west-2 \
  --create-bucket-configuration LocationConstraint=us-west-2
```

## Step 2: Block Public Access

```bash
aws s3api put-public-access-block \
  --bucket floodroute-reports \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

## Step 3: Create DynamoDB Table

```bash
aws dynamodb create-table \
  --table-name FloodReports \
  --attribute-definitions AttributeName=report_id,AttributeType=S \
  --key-schema AttributeName=report_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

Verify:
```bash
aws dynamodb describe-table --table-name FloodReports --region us-east-1
```

## Step 4: Enable Bedrock Model Access

1. Go to AWS Console → Bedrock → Model access
2. Find the desired model (e.g., Claude 3 Sonnet)
3. Click "Request model access"
4. Agree to terms
5. Wait for access approval (usually instant)

Verify via CLI:
```bash
aws bedrock list-foundation-models --region us-east-1 | grep -i claude
```

## Step 5: Create IAM User or Role

### For Local Development (IAM User)

```bash
aws iam create-user --user-name floodroute-dev

# Attach policy (see below)
aws iam put-user-policy --user-name floodroute-dev --policy-name FloodRoute --policy-document file://policy.json

# Create access key
aws iam create-access-key --user-name floodroute-dev
```

### For AWS Lambda/Production (IAM Role)

```bash
aws iam create-role \
  --role-name FloodRouteBackendRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach policy (see below)
aws iam put-role-policy --role-name FloodRouteBackendRole --policy-name FloodRoute --policy-document file://policy.json
```

### IAM Policy (`policy.json`)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "S3ReportStorage",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::floodroute-reports/reports/*"
    },
    {
      "Sid": "DynamoDBReports",
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Scan"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:*:table/FloodReports"
    },
    {
      "Sid": "BedrockInference",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-*"
    }
  ]
}
```

## Step 6: Configure Environment Variables

Create `.env` in the `backend/` directory:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# S3
S3_BUCKET_NAME=floodroute-reports

# DynamoDB
DYNAMODB_TABLE_NAME=FloodReports

# Bedrock
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022

# Upload Configuration
MAX_UPLOAD_SIZE_MB=5
ALLOWED_IMAGE_TYPES=image/jpeg,image/png,image/webp

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Development
DEMO_MODE=false
S3_PRESIGNED_URL_EXPIRY=900
```

## Step 7: Test the Configuration

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt

# Run with real AWS
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` and try submitting a report.

## Step 8: Deploy to Lambda (Optional)

Install serverless framework or use AWS SAM:

```bash
pip install aws-sam-cli
sam init --runtime python3.11 --name floodroute-backend
# Follow prompts
```

Or use Zappa for quick deployment:

```bash
pip install zappa
zappa init
zappa deploy dev
```

## Troubleshooting

### "NoCredentialsError"
Verify AWS CLI is configured:
```bash
aws sts get-caller-identity
```

### "AccessDenied" on DynamoDB/S3
Check IAM policy is attached and model ID is correct:
```bash
aws iam list-attached-user-policies --user-name floodroute-dev
```

### Bedrock model not found
Ensure model access is approved and you're in the correct region:
```bash
aws bedrock list-foundation-models --region us-east-1
```

### "Table does not exist"
Ensure table is created:
```bash
aws dynamodb list-tables --region us-east-1
```

## Cost Estimation (Monthly)

- **S3**: ~$0.10–0.50 (100 reports @ 500KB each)
- **DynamoDB**: $1.25 (pay-per-request, ~10k reads/writes)
- **Bedrock**: ~$5–20 (depends on model and usage)
- **Total**: ~$7–25/month for light usage

## Security Notes

- Never commit `.env` to version control
- Use AWS IAM roles for production (avoid long-lived access keys)
- S3 bucket is private; presigned URLs are time-limited
- Bedrock prompts treat user input as data, not instructions
- Consider enabling S3 versioning for audit trails
