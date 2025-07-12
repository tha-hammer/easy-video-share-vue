# Quick AWS CLI Commands for Lambda Updates

## One-liner to update Lambda environment variables:

```bash
aws lambda update-function-configuration \
  --function-name "easy-video-share-video-processor" \
  --region "us-east-1" \
  --environment 'Variables={ENVIRONMENT=production,DYNAMODB_TABLE=easy-video-share-video-metadata,VIDEO_SEGMENTS_TABLE=easy-video-share-video-segments,S3_BUCKET=easy-video-share-silmari-dev}'
```

## One-liner to update IAM policy:

```bash
aws iam put-role-policy \
  --role-name "easy-video-share-lambda-execution-role" \
  --policy-name "easy-video-share-lambda-policy" \
  --policy-document file://updated-lambda-policy.json
```

## Test the Lambda function:

```bash
aws lambda invoke \
  --function-name "easy-video-share-video-processor" \
  --region "us-east-1" \
  --payload '{"action":"generate_thumbnail","segment_id":"seg_76fabf52-c283-47ed-b8da-87b780dc4a84_032"}' \
  response.json
```

## Check Lambda configuration:

```bash
aws lambda get-function-configuration \
  --function-name "easy-video-share-video-processor" \
  --region "us-east-1"
```

## Check IAM policy:

```bash
aws iam get-role-policy \
  --role-name "easy-video-share-lambda-execution-role" \
  --policy-name "easy-video-share-lambda-policy"
```

## Quick test of segment retrieval:

```bash
aws lambda invoke \
  --function-name "easy-video-share-video-processor" \
  --region "us-east-1" \
  --payload '{"action":"get_segment","segment_id":"seg_76fabf52-c283-47ed-b8da-87b780dc4a84_032"}' \
  segment-test.json
```

## Notes:

- These commands take seconds instead of minutes
- No need to wait for Terraform to apply
- Can be run from any directory with AWS CLI configured
- Make sure you have the correct AWS credentials and region set
