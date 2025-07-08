# Multi-Part Upload Implementation

## Overview

This implementation adds support for multi-part uploads to handle large video files (2GB+) efficiently, especially on mobile devices. The system automatically detects when to use multi-part vs single-part uploads based on file size and device type.

## Features

### 🚀 **Automatic Upload Strategy Selection**

- **Mobile devices**: Uses multi-part for files > 100MB
- **Desktop devices**: Uses multi-part for files > 200MB
- **Small files**: Uses single-part upload for better performance

### 📱 **Mobile-Optimized**

- Adaptive chunk sizes (5MB - 15MB based on file size)
- Limited concurrent uploads (2-4) to prevent overwhelming mobile networks
- Better error recovery and resume capability

### 🖥️ **Desktop-Optimized**

- Larger chunk sizes (10MB - 25MB)
- More concurrent uploads (4-8) for high-bandwidth connections
- Faster upload speeds on good connections

### 🔄 **Parallel Upload Support**

- Uploads multiple chunks simultaneously
- Configurable concurrency limits
- Progress tracking per chunk and overall

## Architecture

### Backend Endpoints

#### 1. Initiate Multi-Part Upload

```http
POST /api/upload/initiate-multipart
```

**Request:**

```json
{
  "filename": "video.mp4",
  "content_type": "video/mp4",
  "file_size": 2147483648
}
```

**Response:**

```json
{
  "upload_id": "abc123...",
  "s3_key": "uploads/job-id/timestamp_video.mp4",
  "job_id": "job-uuid",
  "chunk_size": 15728640,
  "max_concurrent_uploads": 4
}
```

#### 2. Get Part Upload URL

```http
POST /api/upload/part
```

**Request:**

```json
{
  "upload_id": "abc123...",
  "s3_key": "uploads/job-id/timestamp_video.mp4",
  "part_number": 1,
  "content_type": "video/mp4"
}
```

**Response:**

```json
{
  "presigned_url": "https://...",
  "part_number": 1
}
```

#### 3. Complete Multi-Part Upload

```http
POST /api/upload/complete-multipart
```

**Request:**

```json
{
  "upload_id": "abc123...",
  "s3_key": "uploads/job-id/timestamp_video.mp4",
  "job_id": "job-uuid",
  "parts": [
    { "PartNumber": 1, "ETag": "abc123..." },
    { "PartNumber": 2, "ETag": "def456..." }
  ],
  "user_id": "user123",
  "filename": "video.mp4",
  "file_size": 2147483648,
  "title": "My Video",
  "user_email": "user@example.com",
  "content_type": "video/mp4"
}
```

#### 4. Abort Multi-Part Upload

```http
POST /api/upload/abort-multipart
```

**Request:**

```json
{
  "upload_id": "abc123...",
  "s3_key": "uploads/job-id/timestamp_video.mp4"
}
```

### Frontend Implementation

#### Upload Composable (`useVideoUpload.ts`)

The composable automatically handles both single-part and multi-part uploads:

```typescript
// Automatic strategy selection
const shouldUseMultipart = (fileSize: number): boolean => {
  const MB = 1024 * 1024
  const isMobile = /Android|iPhone|iPad|iPod|IEMobile|Opera Mini/i.test(navigator.userAgent)

  if (isMobile) {
    return fileSize > 100 * MB // 100MB threshold for mobile
  } else {
    return fileSize > 200 * MB // 200MB threshold for desktop
  }
}

// Main upload function
const uploadVideo = async (file: File, metadata: VideoMetadata): Promise<void> => {
  if (shouldUseMultipart(file.size)) {
    await uploadVideoMultipart(file, metadata)
  } else {
    await uploadVideoSingle(file, metadata)
  }
}
```

#### Multi-Part Upload Process

1. **Initiate**: Call `initiateMultipartUpload()` to get upload ID and chunk configuration
2. **Split**: Split file into chunks based on recommended chunk size
3. **Upload**: Upload chunks in parallel with concurrency limit
4. **Complete**: Call `completeMultipartUpload()` with all part ETags
5. **Process**: Start video processing job

## Configuration

### Chunk Size Calculation

```python
def calculate_optimal_chunk_size(file_size: int, is_mobile: bool = False) -> tuple[int, int]:
    MB = 1024 * 1024
    GB = 1024 * MB

    if is_mobile:
        # Mobile devices: smaller chunks, fewer concurrent uploads
        if file_size <= 100 * MB:
            return 5 * MB, 2  # 5MB chunks, 2 concurrent
        elif file_size <= 500 * MB:
            return 8 * MB, 3  # 8MB chunks, 3 concurrent
        elif file_size <= 1 * GB:
            return 10 * MB, 3  # 10MB chunks, 3 concurrent
        else:
            return 15 * MB, 4  # 15MB chunks, 4 concurrent
    else:
        # Desktop: larger chunks, more concurrent uploads
        if file_size <= 100 * MB:
            return 10 * MB, 4  # 10MB chunks, 4 concurrent
        elif file_size <= 500 * MB:
            return 15 * MB, 6  # 15MB chunks, 6 concurrent
        elif file_size <= 1 * GB:
            return 20 * MB, 6  # 20MB chunks, 6 concurrent
        else:
            return 25 * MB, 8  # 25MB chunks, 8 concurrent
```

## Usage

### Frontend Integration

The Upload.vue component automatically uses the appropriate upload strategy:

```typescript
const goToUploadStep = async () => {
  if (!validateTitle() || !selectedFile.value) return

  try {
    // Check if we should use multi-part upload
    const shouldUseMultipart = videoUpload.shouldUseMultipart(selectedFile.value.size)

    if (shouldUseMultipart) {
      console.log('📦 Using multi-part upload for large file')
      await videoUpload.initiateMultipartUpload(selectedFile.value)
    } else {
      console.log('📤 Using single-part upload for smaller file')
      await videoUpload.initiateUpload(selectedFile.value)
    }

    // Upload the file (composable handles the rest)
    await videoUpload.uploadVideo(selectedFile.value, metadata)
    currentStep.value = 2
  } catch (e) {
    fileError.value = (e as Error).message
  }
}
```

### Progress Tracking

The system provides detailed progress tracking:

```typescript
interface UploadProgress {
  videoId: string
  filename: string
  totalSize: number
  uploadedSize: number
  percentage: number
  status: 'pending' | 'uploading' | 'completed' | 'error'
  chunkProgress: Map<number, number> // Progress per chunk
  completedChunks: number
  totalChunks: number
}
```

## Testing

### Test Script

Run the test script to verify multi-part upload functionality:

```bash
cd backend
python test_multipart_upload.py
```

This will test:

- Small file uploads (50MB)
- Large file uploads (100MB)
- Abort functionality
- Error handling

### Manual Testing

1. **Mobile Testing**: Use browser dev tools to simulate mobile device
2. **Large File Testing**: Upload files > 100MB to trigger multi-part
3. **Network Testing**: Test with slow network conditions
4. **Error Recovery**: Test abort and resume functionality

## Benefits

### 🚀 **Performance**

- **Parallel uploads**: Multiple chunks upload simultaneously
- **Adaptive sizing**: Optimal chunk sizes for different devices
- **Better throughput**: Especially beneficial for large files

### 📱 **Mobile Experience**

- **Reduced timeouts**: Smaller chunks are less likely to timeout
- **Better error recovery**: Failed chunks can be retried individually
- **Network optimization**: Respects mobile network limitations

### 🔧 **Reliability**

- **Resume capability**: Can resume interrupted uploads
- **Error isolation**: Single chunk failure doesn't fail entire upload
- **Progress tracking**: Detailed progress for each chunk

### 💰 **Cost Optimization**

- **Reduced retries**: Smaller chunks mean fewer retries on failure
- **Better bandwidth utilization**: Parallel uploads maximize available bandwidth
- **S3 optimization**: Multi-part uploads are more efficient for S3

## Error Handling

### Common Scenarios

1. **Network Interruption**: System can retry individual chunks
2. **Chunk Upload Failure**: Failed chunks are retried automatically
3. **Upload Abort**: Clean abort with S3 cleanup
4. **Invalid ETags**: Validation before completing upload

### Recovery Strategies

```typescript
// Automatic retry for failed chunks
const uploadChunkWithRetry = async (chunk: UploadChunk, maxRetries = 3) => {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await uploadChunk(chunk, presignedUrl, progress)
    } catch (error) {
      if (attempt === maxRetries) throw error
      await new Promise((resolve) => setTimeout(resolve, 1000 * attempt))
    }
  }
}
```

## Monitoring

### Metrics to Track

- Upload success rate by file size
- Average upload time by device type
- Chunk retry frequency
- Abort rate and reasons
- Network performance impact

### Logging

The system provides detailed logging for debugging:

```python
print(f"DEBUG: File size: {file_size}, Mobile: {is_mobile}")
print(f"DEBUG: Chunk size: {chunk_size}, Max concurrent: {max_concurrent}")
print(f"DEBUG: Generated upload_id = {upload_id}")
```

## Future Enhancements

### Planned Features

1. **Resume Upload**: Save progress and allow resuming interrupted uploads
2. **Dynamic Chunk Sizing**: Adjust chunk size based on network performance
3. **Upload Queue**: Queue multiple uploads with priority
4. **Bandwidth Detection**: Automatic bandwidth detection and optimization
5. **Compression**: Optional video compression before upload

### Performance Optimizations

1. **Transfer Acceleration**: Enable S3 Transfer Acceleration for faster uploads
2. **CDN Integration**: Use CloudFront for better global performance
3. **Compression**: Implement video compression to reduce upload size
4. **Parallel Processing**: Process video while uploading

## Troubleshooting

### Common Issues

1. **CORS Errors**: Ensure S3 bucket CORS is configured correctly
2. **Presigned URL Expiry**: URLs expire after 1 hour, retry if needed
3. **Chunk Size Issues**: Very large chunks may timeout on slow networks
4. **ETag Mismatch**: Ensure ETags are properly extracted from response headers

### Debug Steps

1. Check browser network tab for failed requests
2. Verify S3 bucket permissions and CORS settings
3. Test with smaller files first
4. Check backend logs for detailed error messages
5. Verify AWS credentials and region settings

## Security Considerations

1. **Presigned URLs**: URLs expire after 1 hour for security
2. **Content Validation**: Validate file types and sizes
3. **User Authentication**: Ensure proper user authentication
4. **S3 Permissions**: Use least privilege principle for S3 access
5. **HTTPS Only**: All uploads use HTTPS for security

This implementation provides a robust, scalable solution for handling large video uploads while maintaining excellent user experience across all device types.
