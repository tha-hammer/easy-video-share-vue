import os
import sys
import requests
import time
import json
import uuid
import logging
import tempfile

API_BASE_URL = "http://localhost:8000/api"
POLL_INTERVAL = 5  # seconds
POLL_TIMEOUT = 600  # seconds (10 minutes)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

def health_check():
    url = f"{API_BASE_URL}/health"
    r = requests.get(url)
    assert r.status_code == 200
    logging.info("API health check passed.")

def upload_video(test_video_path):
    url = f"{API_BASE_URL}/upload/initiate"
    filename = os.path.basename(test_video_path)
    file_size = os.path.getsize(test_video_path)
    content_type = "video/mp4"
    payload = {
        "filename": filename,
        "content_type": content_type,
        "file_size": file_size
    }
    r = requests.post(url, json=payload)
    r.raise_for_status()
    data = r.json()
    presigned_url = data["presigned_url"]
    s3_key = data["s3_key"]
    job_id = data["job_id"]
    logging.info(f"Obtained presigned S3 URL. Uploading {filename}...")
    with open(test_video_path, "rb") as f:
        put_resp = requests.put(presigned_url, data=f, headers={"Content-Type": content_type})
        put_resp.raise_for_status()
    logging.info("Video uploaded to S3 successfully.")
    return s3_key, job_id

def complete_upload(s3_key, job_id, scenario):
    url = f"{API_BASE_URL}/upload/complete"
    payload = {
        "s3_key": s3_key,
        "job_id": job_id,
        "cutting_options": scenario["cutting_options"],
        "text_strategy": scenario["text_strategy"],
        "text_input": scenario["text_input"]
    }
    r = requests.post(url, json=payload)
    r.raise_for_status()
    data = r.json()
    logging.info(f"Job dispatched: {data['job_id']} (status: {data['status']})")
    return data["job_id"]

def poll_job_status(job_id):
    url = f"{API_BASE_URL}/jobs/{job_id}/status"
    start = time.time()
    while True:
        r = requests.get(url)
        if r.status_code == 404:
            logging.info("Job not found yet. Waiting...")
        else:
            r.raise_for_status()
            data = r.json()
            status = data["status"]
            logging.info(f"Job status: {status}")
            if status == "COMPLETED":
                return data
            if status == "FAILED":
                logging.error(f"Job failed: {data.get('error_message')}")
                return data
        if time.time() - start > POLL_TIMEOUT:
            raise TimeoutError("Polling timed out.")
        time.sleep(POLL_INTERVAL)

def download_first_segment(output_urls):
    if not output_urls:
        logging.error("No output URLs to download.")
        return None
    url = output_urls[0]
    r = requests.get(url)
    if r.status_code == 200:
        tmpdir = tempfile.gettempdir()
        out_path = os.path.join(tmpdir, "test_downloaded_segment1.mp4")
        with open(out_path, "wb") as f:
            f.write(r.content)
        logging.info(f"Downloaded first processed segment to {out_path}")
        return out_path
    else:
        logging.error(f"Failed to download processed segment: {r.status_code}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python e2e_full_workflow_test.py path/to/test_video.mp4 [scenario_name]")
        sys.exit(1)
    test_video_path = sys.argv[1]
    scenario_name = sys.argv[2] if len(sys.argv) > 2 else "ONE_FOR_ALL"

    # Define test scenarios
    scenarios = {
        "ONE_FOR_ALL": {
            "cutting_options": {"type": "fixed", "duration_seconds": 10},
            "text_strategy": "one_for_all",
            "text_input": {"strategy": "one_for_all", "base_text": "ONE FOR ALL TEST", "context": None, "unique_texts": None}
        },
        "BASE_VARY": {
            "cutting_options": {"type": "fixed", "duration_seconds": 10},
            "text_strategy": "base_vary",
            "text_input": {"strategy": "base_vary", "base_text": "Try our new product!", "context": "sales, call-to-action", "unique_texts": None}
        },
        "UNIQUE_FOR_ALL": {
            "cutting_options": {"type": "fixed", "duration_seconds": 10},
            "text_strategy": "unique_for_all",
            "text_input": {"strategy": "unique_for_all", "base_text": None, "context": None, "unique_texts": ["First segment text", "Second segment text", "Third segment text"]}
        },
        "RANDOM_CUTTING": {
            "cutting_options": {"type": "random", "min_duration": 5, "max_duration": 15},
            "text_strategy": "one_for_all",
            "text_input": {"strategy": "one_for_all", "base_text": "Random cutting test", "context": None, "unique_texts": None}
        }
    }
    if scenario_name not in scenarios:
        print(f"Unknown scenario: {scenario_name}")
        print(f"Available: {list(scenarios.keys())}")
        sys.exit(1)
    scenario = scenarios[scenario_name]

    print("\n=== 1. API Health Check ===")
    health_check()

    print("\n=== 2. Upload Video to S3 ===")
    s3_key, job_id = upload_video(test_video_path)

    print("\n=== 3. Dispatch Video Processing Job ===")
    celery_job_id = complete_upload(s3_key, job_id, scenario)

    print("\n=== 4. Poll for Job Status ===")
    job_status = poll_job_status(job_id)
    if job_status["status"] == "COMPLETED":
        print("\n=== 5. Download First Processed Segment ===")
        download_first_segment(job_status.get("output_urls"))
    elif job_status["status"] == "FAILED":
        print(f"Job failed: {job_status.get('error_message')}")
    else:
        print(f"Job ended with status: {job_status['status']}")

    print("\n=== 6. Clean Up (Local) ===")
    tmpfile = os.path.join(tempfile.gettempdir(), "test_downloaded_segment1.mp4")
    if os.path.exists(tmpfile):
        os.remove(tmpfile)
        print(f"Removed {tmpfile}")
    print("\nE2E test complete.")

if __name__ == "__main__":
    main()
