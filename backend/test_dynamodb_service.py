import uuid
import requests
from dynamodb_service import create_job_entry, update_job_status, get_job_status

job_id = str(uuid.uuid4())
print(f"Generated job_id: {job_id}")

# 1. Create job entry (QUEUED)
create_job_entry(job_id=job_id, user_id="anonymous", upload_date=None, status="QUEUED", created_at=None, updated_at=None)
print("Created job entry.")

# 2. Update status to PROCESSING
update_job_status(job_id, status="PROCESSING")
print("Updated status to PROCESSING.")

# 3. Update status to COMPLETED with dummy output URLs
# Use a real S3 key format for your bucket
bucket = "easy-video-share-silmari-dev"
s3_key = f"processed/{job_id}/segment1.mp4"
dummy_urls = [f"s3://{bucket}/{s3_key}"]
update_job_status(job_id, status="COMPLETED", output_s3_urls=dummy_urls)
print("Updated status to COMPLETED with output URLs.")

# 4. Retrieve and print job status from DynamoDB
result = get_job_status(job_id)
print("Job status from DynamoDB:")
print(result)

# 5. Call FastAPI endpoint to get presigned download URLs
api_url = f"http://localhost:8000/api/jobs/{job_id}/status"
print(f"\nRequesting job status from FastAPI endpoint: {api_url}")
resp = requests.get(api_url)
print(f"Status code: {resp.status_code}")
print("Response JSON:")
print(resp.json())

# 6. If presigned URLs are present, test downloading the file
data = resp.json()
presigned_urls = data.get("output_urls")
if presigned_urls:
    print("\nTesting download of first presigned URL...")
    url = presigned_urls[0]
    r = requests.get(url)
    print(f"Download status code: {r.status_code}")
    if r.status_code == 200:
        with open("test_downloaded_segment1.mp4", "wb") as f:
            f.write(r.content)
        print("Downloaded file saved as test_downloaded_segment1.mp4")
    else:
        print("Failed to download file from presigned URL.")
else:
    print("No presigned output_urls found in API response.")