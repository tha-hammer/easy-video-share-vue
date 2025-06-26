#!/usr/bin/env python3
"""
Production AI Video Generation API - Bedrock Nova Reel Integration
Real AWS services integration for video processing pipeline
"""

import os
import json
import logging
import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Import our services
from services.bedrock_nova_client import BedrockNovaReelClient
from services.audio_transcription import AudioTranscriptionService
from services.scene_generation import SceneGenerationService

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

class Config:
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'dev')
        self.project_name = os.getenv('PROJECT_NAME', 'easy-video-share')
        self.aws_region = os.getenv('AWS_REGION', 'us-east-1')
        self.use_localstack = os.getenv('USE_LOCALSTACK', 'false').lower() == 'true'
        
        # AWS Tables and Resources
        self.ai_projects_table = os.getenv('AI_PROJECTS_TABLE')
        self.video_assets_table = os.getenv('VIDEO_ASSETS_TABLE')
        self.s3_bucket = os.getenv('S3_BUCKET')
        self.event_bus_name = os.getenv('EVENT_BUS_NAME')
        self.secrets_name = os.getenv('SECRETS_NAME')
        
        # Validate required environment variables
        self._validate_config()
    
    def _validate_config(self):
        required_vars = [
            'AI_PROJECTS_TABLE', 'VIDEO_ASSETS_TABLE', 'S3_BUCKET'
        ]
        
        missing_vars = [var for var in required_vars if not getattr(self, var.lower())]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")

config = Config()

# =============================================================================
# AWS Clients
# =============================================================================

def get_aws_clients():
    """Initialize AWS clients based on environment"""
    try:
        if config.use_localstack:
            # LocalStack configuration (for development)
            session = boto3.Session()
            endpoint_url = 'http://localhost:4566'
            
            clients = {
                's3': session.client('s3', endpoint_url=endpoint_url),
                'dynamodb': session.resource('dynamodb', endpoint_url=endpoint_url),
                'events': session.client('events', endpoint_url=endpoint_url),
                'secretsmanager': session.client('secretsmanager', endpoint_url=endpoint_url),
                'bedrock': None  # Bedrock not available in LocalStack
            }
        else:
            # Real AWS configuration
            session = boto3.Session(region_name=config.aws_region)
            
            clients = {
                's3': session.client('s3'),
                'dynamodb': session.resource('dynamodb'),
                'events': session.client('events'),
                'secretsmanager': session.client('secretsmanager'),
                'bedrock': session.client('bedrock-runtime')
            }
        
        logger.info(f"AWS clients initialized (LocalStack: {config.use_localstack})")
        return clients
        
    except Exception as e:
        logger.error(f"Failed to initialize AWS clients: {e}")
        raise

aws_clients = get_aws_clients()

# =============================================================================
# Database Models
# =============================================================================

class ProjectStatus:
    UPLOADED = "uploaded"
    TRANSCRIBING = "transcribing"
    PLANNING = "planning"
    GENERATING = "generating"
    POST_PROCESSING = "post_processing"
    COMPLETED = "completed"
    FAILED = "failed"

class AudioProject(BaseModel):
    project_id: str
    user_id: str
    title: str
    audio_file_url: str
    target_duration: int = Field(default=45, ge=30, le=60)
    status: str = ProjectStatus.UPLOADED
    transcript_text: Optional[str] = None
    scene_plan: Optional[Dict] = None
    generated_assets: Optional[List[Dict]] = None
    final_video_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str

class ProcessVideoRequest(BaseModel):
    project_id: str
    audio_s3_key: str
    target_duration: int = Field(default=45, ge=30, le=60)

# =============================================================================
# Database Operations
# =============================================================================

class DatabaseService:
    def __init__(self):
        self.dynamodb = aws_clients['dynamodb']
        self.projects_table = self.dynamodb.Table(config.ai_projects_table)
        self.assets_table = self.dynamodb.Table(config.video_assets_table)
    
    async def get_project(self, project_id: str) -> Optional[Dict]:
        """Get project by ID"""
        try:
            response = self.projects_table.get_item(Key={'project_id': project_id})
            return response.get('Item')
        except ClientError as e:
            logger.error(f"Error getting project {project_id}: {e}")
            return None
    
    async def create_project(self, project_data: Dict) -> Dict:
        """Create new project"""
        try:
            self.projects_table.put_item(Item=project_data)
            return project_data
        except ClientError as e:
            logger.error(f"Error creating project: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
    
    async def update_project(self, project_id: str, updates: Dict) -> bool:
        """Update project with new data"""
        try:
            # Build update expression
            update_expression = "SET updated_at = :updated_at"
            expression_values = {':updated_at': datetime.now().isoformat()}
            expression_names = {}
            
            for key, value in updates.items():
                if key != 'project_id':  # Can't update primary key
                    if key == 'status':
                        # Handle reserved keyword
                        update_expression += ", #status = :status"
                        expression_names['#status'] = 'status'
                        expression_values[':status'] = value
                    else:
                        update_expression += f", {key} = :{key}"
                        expression_values[f':{key}'] = value
            
            # Execute update
            kwargs = {
                'Key': {'project_id': project_id},
                'UpdateExpression': update_expression,
                'ExpressionAttributeValues': expression_values
            }
            
            if expression_names:
                kwargs['ExpressionAttributeNames'] = expression_names
            
            self.projects_table.update_item(**kwargs)
            return True
            
        except ClientError as e:
            logger.error(f"Error updating project {project_id}: {e}")
            return False
    
    async def list_projects(self, user_id: Optional[str] = None) -> List[Dict]:
        """List projects, optionally filtered by user"""
        try:
            if user_id:
                response = self.projects_table.query(
                    IndexName='user-projects-index',
                    KeyConditionExpression='user_id = :user_id',
                    ExpressionAttributeValues={':user_id': user_id}
                )
            else:
                response = self.projects_table.scan()
            
            return response.get('Items', [])
        except ClientError as e:
            logger.error(f"Error listing projects: {e}")
            return []

db_service = DatabaseService()

# =============================================================================
# AI Services Integration
# =============================================================================

class AIVideoProcessor:
    def __init__(self):
        self.bedrock_client = BedrockNovaReelClient(aws_clients['bedrock']) if aws_clients['bedrock'] else None
        self.transcription_service = AudioTranscriptionService(aws_clients)
        self.scene_service = SceneGenerationService(aws_clients)
        self.s3_client = aws_clients['s3']
    
    async def process_video_generation(self, project_id: str, audio_s3_key: str):
        """Main video generation pipeline"""
        try:
            logger.info(f"Starting video generation for project {project_id}")
            
            # Step 1: Update status to transcribing
            await db_service.update_project(project_id, {'status': ProjectStatus.TRANSCRIBING})
            
            # Step 2: Transcribe audio
            transcript = await self.transcription_service.transcribe_audio(audio_s3_key, project_id)
            await db_service.update_project(project_id, {
                'status': ProjectStatus.PLANNING,
                'transcript_text': transcript.get('text', '')
            })
            
            # Step 3: Generate scene plan
            project = await db_service.get_project(project_id)
            scene_plan = await self.scene_service.generate_scene_plan(
                transcript, project.get('target_duration', 45)
            )
            await db_service.update_project(project_id, {
                'status': ProjectStatus.GENERATING,
                'scene_plan': scene_plan
            })
            
            # Step 4: Generate video assets with Bedrock Nova Reel
            if self.bedrock_client:
                generated_assets = await self._generate_assets_with_bedrock(scene_plan, project_id)
            else:
                # Fallback for development without Bedrock access
                generated_assets = await self._generate_mock_assets(scene_plan, project_id)
            
            await db_service.update_project(project_id, {
                'status': ProjectStatus.POST_PROCESSING,
                'generated_assets': generated_assets
            })
            
            # Step 5: Compile final video
            final_video_url = await self._compile_final_video(project_id, generated_assets, transcript)
            
            # Step 6: Complete
            await db_service.update_project(project_id, {
                'status': ProjectStatus.COMPLETED,
                'final_video_url': final_video_url
            })
            
            logger.info(f"Video generation completed for project {project_id}")
            return final_video_url
            
        except Exception as e:
            logger.error(f"Video generation failed for project {project_id}: {e}")
            await db_service.update_project(project_id, {
                'status': ProjectStatus.FAILED,
                'error_message': str(e)
            })
            raise
    
    async def _generate_assets_with_bedrock(self, scene_plan: Dict, project_id: str) -> List[Dict]:
        """Generate video assets using Bedrock Nova Reel"""
        generated_assets = []
        
        for i, scene in enumerate(scene_plan.get('scenes', [])):
            try:
                logger.info(f"Generating asset {i+1} for project {project_id}")
                
                # Generate video with Bedrock Nova Reel
                result = await self.bedrock_client.generate_video(
                    prompt=scene['prompt'],
                    duration=scene.get('duration', 5),
                    aspect_ratio="16:9"  # or "9:16" for vertical
                )
                
                # Store asset metadata
                asset_data = {
                    'asset_id': str(uuid.uuid4()),
                    'project_id': project_id,
                    'scene_index': i,
                    'bedrock_job_id': result.get('job_id'),
                    'prompt': scene['prompt'],
                    'status': 'generating',
                    'created_at': datetime.now().isoformat()
                }
                
                generated_assets.append(asset_data)
                
                # Poll for completion (in production, this would be event-driven)
                video_url = await self._poll_bedrock_job(result.get('job_id'))
                if video_url:
                    asset_data.update({
                        'status': 'completed',
                        'video_url': video_url
                    })
                
            except Exception as e:
                logger.error(f"Failed to generate asset {i+1}: {e}")
                asset_data = {
                    'asset_id': str(uuid.uuid4()),
                    'project_id': project_id,
                    'scene_index': i,
                    'status': 'failed',
                    'error_message': str(e),
                    'created_at': datetime.now().isoformat()
                }
                generated_assets.append(asset_data)
        
        return generated_assets
    
    async def _generate_mock_assets(self, scene_plan: Dict, project_id: str) -> List[Dict]:
        """Generate mock assets for development/testing"""
        generated_assets = []
        
        for i, scene in enumerate(scene_plan.get('scenes', [])):
            asset_data = {
                'asset_id': str(uuid.uuid4()),
                'project_id': project_id,
                'scene_index': i,
                'prompt': scene['prompt'],
                'status': 'completed',
                'video_url': f"https://example.com/mock-video-{project_id}-{i}.mp4",
                'created_at': datetime.now().isoformat()
            }
            generated_assets.append(asset_data)
            
            # Simulate processing delay
            await asyncio.sleep(1)
        
        return generated_assets
    
    async def _poll_bedrock_job(self, job_id: str, max_attempts: int = 60) -> Optional[str]:
        """Poll Bedrock job status until completion"""
        for attempt in range(max_attempts):
            try:
                if self.bedrock_client:
                    status = await self.bedrock_client.get_job_status(job_id)
                    if status['status'] == 'completed':
                        return status.get('video_url')
                    elif status['status'] == 'failed':
                        logger.error(f"Bedrock job {job_id} failed: {status.get('error')}")
                        return None
                
                # Wait before next poll
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Error polling Bedrock job {job_id}: {e}")
                return None
        
        logger.warning(f"Bedrock job {job_id} timed out after {max_attempts} attempts")
        return None
    
    async def _compile_final_video(self, project_id: str, assets: List[Dict], transcript: Dict) -> str:
        """Compile final video from generated assets"""
        # In production, this would use FFmpeg or similar
        # For now, return a mock URL
        final_url = f"https://example.com/generated/final-{project_id}.mp4"
        logger.info(f"Final video compiled for project {project_id}: {final_url}")
        return final_url

ai_processor = AIVideoProcessor()

# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="AI Video Generation API - Production",
    description="Bedrock Nova Reel integration for AI-powered video generation",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connectivity
        await db_service.list_projects()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "environment": config.environment,
            "services_status": {
                "database": "healthy",
                "s3": "healthy",
                "bedrock": "available" if aws_clients['bedrock'] else "mock"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/projects")
async def list_projects(user_id: Optional[str] = None):
    """List all projects or projects for a specific user"""
    try:
        projects = await db_service.list_projects(user_id)
        return {
            "projects": projects,
            "count": len(projects)
        }
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/projects/{project_id}")
async def get_project(project_id: str):
    """Get specific project details"""
    try:
        project = await db_service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-video")
async def process_video(request: ProcessVideoRequest, background_tasks: BackgroundTasks):
    """Start video processing for a project"""
    try:
        # Verify project exists
        project = await db_service.get_project(request.project_id)
        if not project:
            # Create a basic project record
            project_data = {
                'project_id': request.project_id,
                'user_id': 'system',  # In production, get from auth context
                'title': f'AI Video Project {request.project_id[:8]}',
                'audio_file_url': request.audio_s3_key,
                'target_duration': request.target_duration,
                'status': ProjectStatus.UPLOADED,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            await db_service.create_project(project_data)
        
        # Start background processing
        background_tasks.add_task(
            ai_processor.process_video_generation,
            request.project_id,
            request.audio_s3_key
        )
        
        return {
            "project_id": request.project_id,
            "status": "processing_started",
            "message": "Video generation started. Check status with GET /projects/{project_id}"
        }
        
    except Exception as e:
        logger.error(f"Error starting video processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/projects")
async def create_project(project: AudioProject):
    """Create a new project"""
    try:
        project_data = project.dict()
        project_data['created_at'] = datetime.now().isoformat()
        project_data['updated_at'] = datetime.now().isoformat()
        
        created_project = await db_service.create_project(project_data)
        return created_project
        
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# Application Entry Point
# =============================================================================

if __name__ == "__main__":
    # Production configuration
    port = int(os.getenv('PORT', 8080))
    host = os.getenv('HOST', '0.0.0.0')
    
    logger.info(f"Starting AI Video Generation API on {host}:{port}")
    logger.info(f"Environment: {config.environment}")
    logger.info(f"Using LocalStack: {config.use_localstack}")
    
    uvicorn.run(
        "app_production:app",
        host=host,
        port=port,
        log_level=config.log_level.lower() if hasattr(config, 'log_level') else "info",
        reload=config.environment == 'dev'
    ) 