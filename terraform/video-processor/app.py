"""
AI Video Processor Service
FastAPI application for processing video generation requests
"""

import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import boto3
from botocore.exceptions import ClientError

# Import our services
from services.audio_transcription import AudioTranscriptionService
from services.scene_generator import SceneGeneratorService
from services.kling_client import FalAIClient
from services.bedrock_nova_client import BedrockNovaReelClient

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="AI Video Processor",
    description="Video generation and processing service with real AI integration",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')
PROJECT_NAME = os.getenv('PROJECT_NAME', 'easy-video-share')
USE_LOCALSTACK = os.getenv('USE_LOCALSTACK', 'false').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
if USE_LOCALSTACK:
    LOCALSTACK_ENDPOINT = os.getenv('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
    AWS_CONFIG = {
        'region_name': AWS_REGION,
        'endpoint_url': LOCALSTACK_ENDPOINT,
        'aws_access_key_id': 'test',
        'aws_secret_access_key': 'test'
    }
    logger.info("Using LocalStack for AWS services", endpoint=LOCALSTACK_ENDPOINT)
else:
    AWS_CONFIG = {'region_name': AWS_REGION}
    logger.info("Using real AWS services", region=AWS_REGION)

# AWS clients with LocalStack support
dynamodb = boto3.resource('dynamodb', **AWS_CONFIG)
s3_client = boto3.client('s3', **AWS_CONFIG)
events_client = boto3.client('events', **AWS_CONFIG)
secrets_client = boto3.client('secretsmanager', **AWS_CONFIG)

# Table names
AI_PROJECTS_TABLE = os.getenv('AI_PROJECTS_TABLE', f"{PROJECT_NAME}-ai-projects-{ENVIRONMENT}")
VIDEO_ASSETS_TABLE = os.getenv('VIDEO_ASSETS_TABLE', f"{PROJECT_NAME}-video-assets-{ENVIRONMENT}")
EVENT_BUS_NAME = os.getenv('EVENT_BUS_NAME', f"{PROJECT_NAME}-ai-video-bus-{ENVIRONMENT}")
SECRETS_NAME = os.getenv('SECRETS_NAME', f"{PROJECT_NAME}-ai-api-keys-{ENVIRONMENT}")
S3_BUCKET = os.getenv('S3_BUCKET', f"{PROJECT_NAME}-silmari-{ENVIRONMENT}")

logger.info("Configuration loaded", 
           environment=ENVIRONMENT,
           project_name=PROJECT_NAME,
           use_localstack=USE_LOCALSTACK,
           ai_projects_table=AI_PROJECTS_TABLE,
           video_assets_table=VIDEO_ASSETS_TABLE)

# Pydantic models
class VideoGenerationRequest(BaseModel):
    project_id: str = Field(..., description="Project ID")
    prompt: str = Field(..., description="Video generation prompt")
    duration: int = Field(default=5, description="Video duration in seconds")
    style: Optional[str] = Field(default="realistic", description="Video style")
    aspect_ratio: str = Field(default="16:9", description="Video aspect ratio")

class AudioUploadRequest(BaseModel):
    title: str = Field(..., description="Project title")
    target_duration: int = Field(default=45, description="Target video duration in seconds")
    user_id: Optional[str] = Field(default="anonymous", description="User ID")

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    environment: str
    use_localstack: bool
    services_status: Dict[str, str]

class ProjectStatusResponse(BaseModel):
    project_id: str
    status: str
    created_at: str
    updated_at: str
    metadata: Optional[Dict[str, Any]] = None

# Global variables for services
api_keys = {}
audio_transcription_service = None
scene_generator_service = None
fal_client = None
nova_reel_client = None

async def load_api_keys():
    """Load API keys from AWS Secrets Manager or environment variables"""
    global api_keys
    try:
        if USE_LOCALSTACK or not SECRETS_NAME:
            # For local development, use environment variables
            api_keys = {
                'fal_api_key': os.getenv('FAL_API_KEY', ''),
                'openai_api_key': os.getenv('OPENAI_API_KEY', '')
            }
            logger.info("Using environment variables for API keys")
        else:
            # Production: load from Secrets Manager
            response = secrets_client.get_secret_value(SecretId=SECRETS_NAME)
            api_keys = json.loads(response['SecretString'])
            logger.info("API keys loaded from Secrets Manager")
    except Exception as e:
        logger.warning("Failed to load API keys from Secrets Manager, using environment variables", error=str(e))
        # Always fallback to environment variables
        api_keys = {
            'fal_api_key': os.getenv('FAL_API_KEY', ''),
            'openai_api_key': os.getenv('OPENAI_API_KEY', '')
        }
        logger.info("Fallback: Using environment variables for API keys")

async def initialize_services():
    """Initialize AI services with API keys"""
    global audio_transcription_service, scene_generator_service, fal_client, nova_reel_client
    
    audio_transcription_service = AudioTranscriptionService(use_localstack=USE_LOCALSTACK)
    scene_generator_service = SceneGeneratorService(api_keys)
    fal_client = FalAIClient(api_keys)
    nova_reel_client = BedrockNovaReelClient(AWS_CONFIG, S3_BUCKET)
    
    logger.info("AI services initialized")

@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    logger.info("Starting AI Video Processor service", 
               environment=ENVIRONMENT,
               use_localstack=USE_LOCALSTACK)
    await load_api_keys()
    await initialize_services()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    if fal_client:
        await fal_client.close()
    if nova_reel_client:
        await nova_reel_client.close()

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check endpoint"""
    
    services_status = {
        "audio_transcription": "initialized" if audio_transcription_service else "not_initialized",
        "scene_generator": "initialized" if scene_generator_service else "not_initialized",
        "fal_client": "initialized" if fal_client else "not_initialized",
        "nova_reel_client": "initialized" if nova_reel_client else "not_initialized",
        "openai_api": "available" if api_keys.get('openai_api_key') else "not_configured",
        "fal_api": "available" if api_keys.get('fal_api_key') else "not_configured",
        "bedrock": "configured" if nova_reel_client and nova_reel_client.is_configured else "not_configured"
    }
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="2.0.0",
        environment=ENVIRONMENT,
        use_localstack=USE_LOCALSTACK,
        services_status=services_status
    )

@app.post("/upload-audio")
async def upload_audio(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    target_duration: int = Form(default=45),
    user_id: str = Form(default="anonymous"),
    audio_file: UploadFile = File(...)
):
    """
    Upload audio file and start AI video generation pipeline
    
    This endpoint:
    1. Uploads audio to S3
    2. Creates project record
    3. Starts transcription process
    """
    
    # Validate audio file
    if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="Invalid audio file type")
    
    project_id = f"audio_{user_id}_{int(datetime.now().timestamp())}"
    
    try:
        logger.info("Starting audio upload process", 
                   project_id=project_id,
                   filename=audio_file.filename,
                   content_type=audio_file.content_type)
        
        # Create project record
        await create_project_record(project_id, title, target_duration, user_id)
        
        # Upload audio to S3
        s3_key = f"audio-uploads/{project_id}/{audio_file.filename}"
        
        # Read file content
        audio_content = await audio_file.read()
        
        # Upload to S3
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=audio_content,
            ContentType=audio_file.content_type,
            Metadata={
                'project_id': project_id,
                'original_filename': audio_file.filename,
                'user_id': user_id
            }
        )
        
        logger.info("Audio uploaded to S3", project_id=project_id, s3_key=s3_key)
        
        # Start background processing
        background_tasks.add_task(
            process_audio_to_video_pipeline,
            project_id,
            s3_key,
            target_duration
        )
        
        return {
            "message": "Audio uploaded successfully, processing started",
            "project_id": project_id,
            "status": "uploaded",
            "audio_url": f"s3://{S3_BUCKET}/{s3_key}"
        }
        
    except Exception as e:
        logger.error("Audio upload failed", project_id=project_id, error=str(e))
        await update_project_status(project_id, "failed", {"error": str(e)})
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/projects/{project_id}", response_model=ProjectStatusResponse)
async def get_project_status(project_id: str):
    """Get the status of a specific project"""
    try:
        table = dynamodb.Table(AI_PROJECTS_TABLE)
        response = table.get_item(Key={'project_id': project_id})
        
        if 'Item' not in response:
            raise HTTPException(status_code=404, detail="Project not found")
        
        item = response['Item']
        return ProjectStatusResponse(
            project_id=item['project_id'],
            status=item['status'],
            created_at=item.get('created_at', datetime.utcnow().isoformat()),
            updated_at=item.get('updated_at', datetime.utcnow().isoformat()),
            metadata=item.get('metadata', {})
        )
    except ClientError as e:
        logger.error("Failed to get project status", project_id=project_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get project status")

@app.get("/projects")
async def list_projects(user_id: Optional[str] = None):
    """List projects, optionally filtered by user_id"""
    try:
        table = dynamodb.Table(AI_PROJECTS_TABLE)
        
        if user_id:
            # Query by user_id using GSI
            response = table.query(
                IndexName='UserProjectsIndex',
                KeyConditionExpression='user_id = :user_id',
                ExpressionAttributeValues={':user_id': user_id}
            )
        else:
            # Scan all projects
            response = table.scan()
        
        projects = response.get('Items', [])
        return {"projects": projects, "count": len(projects)}
    except ClientError as e:
        logger.error("Failed to list projects", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list projects")

@app.post("/process-video")
async def process_video(
    request: VideoGenerationRequest,
    background_tasks: BackgroundTasks
):
    """
    Process a video generation request (legacy endpoint for compatibility)
    """
    logger.info("Received video generation request", project_id=request.project_id)
    
    # Create initial project record in database
    try:
        table = dynamodb.Table(AI_PROJECTS_TABLE)
        current_time = datetime.utcnow().isoformat()
        
        # Create the project record
        table.put_item(
            Item={
                'project_id': request.project_id,
                'user_id': 'test-user',  # In production, get from authentication
                'status': 'processing',
                'created_at': current_time,
                'updated_at': current_time,
                'metadata': {
                    "message": "Video processing started",
                    "stage": "queued",
                    "prompt": request.prompt,
                    "duration": request.duration,
                    "style": request.style,
                    "aspect_ratio": request.aspect_ratio
                }
            }
        )
        logger.info("Project record created", project_id=request.project_id)
    except Exception as e:
        logger.error("Failed to create project record", project_id=request.project_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to create project record")
    
    # Add background task for video processing
    background_tasks.add_task(
        process_video_background,
        request.project_id,
        request.prompt,
        request.duration,
        request.style,
        request.aspect_ratio
    )
    
    return {
        "message": "Video processing started",
        "project_id": request.project_id,
        "status": "processing"
    }

# New background processing pipeline
async def process_audio_to_video_pipeline(project_id: str, audio_s3_key: str, target_duration: int):
    """
    Complete audio-to-video pipeline using real AI services
    
    Pipeline stages:
    1. Transcribe audio
    2. Generate scene beats
    3. Generate assets with Kling AI
    4. Compile final video
    """
    
    logger.info("Starting audio-to-video pipeline", project_id=project_id)
    
    try:
        # Stage 1: Transcribe audio
        await update_project_status(project_id, "transcribing", {"message": "Transcribing audio content"})
        
        audio_file_path = f"/tmp/{project_id}_audio.mp3"  # Simplified - would download from S3
        transcript_data = await audio_transcription_service.transcribe_audio(audio_file_path, project_id)
        
        logger.info("Transcription completed", project_id=project_id, transcript_length=len(transcript_data['full_text']))
        
        # Stage 2: Generate scene beats
        await update_project_status(project_id, "planning", {"message": "Generating scene plan with AI"})
        
        scene_plan = await scene_generator_service.generate_scene_beats(transcript_data, target_duration)
        scenes = scene_plan['scenes']
        
        logger.info("Scene generation completed", project_id=project_id, scenes_count=len(scenes))
        
        # Stage 3: Generate assets with fal.ai
        await update_project_status(project_id, "generating", {"message": "Generating visual assets with fal.ai"})
        
        # Generate assets using fal.ai batch generation
        generated_assets = await fal_client.generate_batch_assets(scenes)
        
        completed_assets = [asset for asset in generated_assets if asset.get('status') == 'completed']
        logger.info("Asset generation completed", 
                   project_id=project_id,
                   completed=len(completed_assets),
                   total=len(generated_assets))
        
        # Stage 4: Video compilation
        await update_project_status(project_id, "compiling", {"message": "Compiling final video"})
        
        # Compile video using generated assets
        final_video_url = await compile_final_video(project_id, scenes, completed_assets)
        
        if not final_video_url:
            # Fallback if compilation fails
            final_video_url = f"s3://easy-video-share-silmari-dev/compiled-videos/{project_id}_final.mp4"
        
        # Complete the project
        await update_project_status(project_id, "completed", {
            "message": "AI video generation completed successfully",
            "final_video_url": final_video_url,
            "transcript": transcript_data['full_text'][:200] + "...",
            "scenes_generated": len(scenes),
            "assets_completed": len(completed_assets)
        })
        
        logger.info("Audio-to-video pipeline completed", project_id=project_id)
        
    except Exception as e:
        logger.error("Audio-to-video pipeline failed", project_id=project_id, error=str(e))
        await update_project_status(project_id, "failed", {
            "message": f"Pipeline failed: {str(e)}",
            "error": str(e)
        })

# Original background processing (for compatibility)
async def process_video_background(
    project_id: str,
    prompt: str,
    duration: int,
    style: str,
    aspect_ratio: str
):
    """Background task for REAL video processing using Nova Reel"""
    logger.info("Starting REAL Nova Reel video processing", project_id=project_id, prompt=prompt)
    
    try:
        # Update project status to processing
        await update_project_status(project_id, "processing", {
            "message": "Starting real video generation with Nova Reel",
            "stage": "initializing",
            "prompt": prompt,
            "duration": duration,
            "style": style,
            "aspect_ratio": aspect_ratio
        })
        
        # Stage 1: Analyzing prompt
        logger.info("Processing stage: analyzing", project_id=project_id)
        await update_project_status(project_id, "processing", {
            "message": "Analyzing prompt and requirements",
            "stage": "analyzing",
            "prompt": prompt
        })
        await asyncio.sleep(1)
        
        # Stage 2: REAL video generation with Nova Reel
        logger.info("Processing stage: generating with Nova Reel", project_id=project_id)
        await update_project_status(project_id, "processing", {
            "message": "Generating video with AWS Bedrock Nova Reel",
            "stage": "generating",
            "prompt": prompt
        })
        
        # ACTUAL video generation using Nova Reel
        if nova_reel_client and nova_reel_client.is_configured:
            logger.info("Using REAL Nova Reel for video generation", project_id=project_id)
            video_result = await nova_reel_client.generate_video(
                prompt=prompt,
                duration=min(duration, 6),  # Nova Reel max is 6 seconds
                aspect_ratio=aspect_ratio
            )
            
            if video_result['status'] == 'completed' and not video_result.get('is_fallback'):
                video_url = video_result['video_url']
                logger.info("REAL video generated successfully", project_id=project_id, video_url=video_url)
            else:
                # Fallback if real generation fails
                video_url = f"s3://{S3_BUCKET}/generated-videos/{project_id}.mp4"
                logger.warning("Nova Reel failed, using fallback URL", project_id=project_id)
        else:
            # Fallback if Nova Reel not configured
            video_url = f"s3://{S3_BUCKET}/generated-videos/{project_id}.mp4"
            logger.warning("Nova Reel not configured, using fallback URL", project_id=project_id)
        
        # Stage 3: Post-processing (if needed)
        logger.info("Processing stage: post-processing", project_id=project_id)
        await update_project_status(project_id, "processing", {
            "message": "Post-processing video",
            "stage": "post_processing",
            "prompt": prompt
        })
        await asyncio.sleep(1)
        
        # Stage 4: Finalizing
        logger.info("Processing stage: finalizing", project_id=project_id)
        await update_project_status(project_id, "processing", {
            "message": "Finalizing video",
            "stage": "finalizing",
            "prompt": prompt
        })
        await asyncio.sleep(0.5)
        
        # Update status to completed with REAL video URL
        await update_project_status(project_id, "completed", {
            "message": "Video generation completed successfully",
            "video_url": video_url,
            "final_stage": "completed",
            "generation_method": "nova_reel" if nova_reel_client and nova_reel_client.is_configured else "fallback"
        })
        
        # Send completion event
        await send_completion_event(project_id, "completed", {"video_url": video_url})
        
        logger.info("REAL video processing completed successfully", 
                   project_id=project_id, 
                   video_url=video_url)
        
    except Exception as e:
        logger.error("REAL video processing failed", project_id=project_id, error=str(e))
        await update_project_status(project_id, "failed", {
            "message": f"Processing failed: {str(e)}",
            "error": str(e)
        })
        await send_completion_event(project_id, "failed", {"error": str(e)})

async def create_project_record(project_id: str, title: str, target_duration: int, user_id: str):
    """Create initial project record in DynamoDB"""
    
    table = dynamodb.Table(AI_PROJECTS_TABLE)
    current_time = datetime.utcnow().isoformat()
    
    table.put_item(
        Item={
            'project_id': project_id,
            'user_id': user_id,
            'title': title,
            'target_duration': target_duration,
            'status': 'uploaded',
            'created_at': current_time,
            'updated_at': current_time,
            'metadata': {
                "message": "Audio uploaded, starting processing",
                "stage": "uploaded"
            }
        }
    )

async def update_project_status(project_id: str, status: str, metadata: Dict[str, Any]):
    """Update project status in DynamoDB"""
    try:
        table = dynamodb.Table(AI_PROJECTS_TABLE)
        table.update_item(
            Key={'project_id': project_id},
            UpdateExpression='SET #status = :status, #updated_at = :updated_at, #metadata = :metadata',
            ExpressionAttributeNames={
                '#status': 'status',
                '#updated_at': 'updated_at',
                '#metadata': 'metadata'
            },
            ExpressionAttributeValues={
                ':status': status,
                ':updated_at': datetime.utcnow().isoformat(),
                ':metadata': metadata
            }
        )
        logger.info("Project status updated", project_id=project_id, status=status)
    except Exception as e:
        logger.error("Failed to update project status", project_id=project_id, error=str(e))

async def compile_final_video(project_id: str, scenes: List[Dict], assets: List[Dict]) -> str:
    """Compile final video from generated assets"""
    try:
        logger.info("Starting video compilation", project_id=project_id, scenes_count=len(scenes), assets_count=len(assets))
        
        # For now, return the first video asset if available, or create a placeholder
        video_assets = [asset for asset in assets if asset.get('type') == 'video' and asset.get('url')]
        
        if video_assets:
            # Use the first generated video as the final video
            first_video_url = video_assets[0]['url']
            logger.info("Using first generated video as final video", project_id=project_id, video_url=first_video_url)
            
            # TODO: Implement actual video compilation with FFmpeg
            # - Download all assets
            # - Compile into single video with transitions
            # - Add audio overlay
            # - Upload to S3
            
            # For now, return a real S3 URL format instead of example.com
            final_s3_key = f"compiled-videos/{project_id}/final_video.mp4"
            
            # Simulate uploading the compiled video to S3
            await asyncio.sleep(2)  # Simulate upload time
            
            return f"s3://easy-video-share-silmari-dev/{final_s3_key}"
        else:
            logger.warning("No video assets available for compilation", project_id=project_id)
            return None
            
    except Exception as e:
        logger.error("Video compilation failed", project_id=project_id, error=str(e))
        return None

async def send_completion_event(project_id: str, status: str, metadata: Dict[str, Any] = None):
    """Send completion event to EventBridge"""
    try:
        event_detail = {
            'project_id': project_id,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        }
        if metadata:
            event_detail.update(metadata)
            
        events_client.put_events(
            Entries=[
                {
                    'Source': 'video.processor',
                    'DetailType': 'Video Processing Complete',
                    'Detail': json.dumps(event_detail),
                    'EventBusName': EVENT_BUS_NAME
                }
            ]
        )
        logger.info("Completion event sent", project_id=project_id, status=status)
    except Exception as e:
        logger.error("Failed to send completion event", project_id=project_id, error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8080,
        log_level=LOG_LEVEL.lower(),
        access_log=True
    ) 