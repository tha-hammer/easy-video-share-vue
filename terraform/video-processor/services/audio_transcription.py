"""
Audio Transcription Service
Handles audio file processing and transcription using AWS Transcribe
"""

import asyncio
import os
import json
import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
from pydub import AudioSegment
import structlog

logger = structlog.get_logger(__name__)

class AudioTranscriptionService:
    """Service for transcribing audio files using AWS Transcribe or local fallback"""
    
    def __init__(self, use_localstack: bool = False):
        self.use_localstack = use_localstack
        
        # AWS clients
        if use_localstack:
            self.transcribe = boto3.client('transcribe',
                endpoint_url=os.getenv('LOCALSTACK_ENDPOINT', 'http://localhost:4566'),
                region_name='us-east-1',
                aws_access_key_id='test',
                aws_secret_access_key='test'
            )
            self.s3 = boto3.client('s3',
                endpoint_url=os.getenv('LOCALSTACK_ENDPOINT', 'http://localhost:4566'),
                region_name='us-east-1',
                aws_access_key_id='test',
                aws_secret_access_key='test'
            )
        else:
            self.transcribe = boto3.client('transcribe')
            self.s3 = boto3.client('s3')
        
        # Configuration
        self.bucket_name = os.getenv('S3_BUCKET', 'easy-video-share-silmari-dev')
        self.supported_formats = ['mp3', 'wav', 'm4a', 'aac', 'ogg', 'flac']
        
    async def transcribe_audio(self, audio_file_path: str, project_id: str) -> Dict:
        """
        Transcribe audio file and return detailed transcript with timestamps
        
        Args:
            audio_file_path: Path to the audio file (local or S3)
            project_id: Project identifier for tracking
            
        Returns:
            Dict containing transcript data with segments and metadata
        """
        logger.info("Starting audio transcription", project_id=project_id, file_path=audio_file_path)
        
        try:
            if self.use_localstack or not await self._can_use_aws_transcribe():
                # Use local speech recognition for development
                return await self._transcribe_local(audio_file_path, project_id)
            else:
                # Use AWS Transcribe for production
                return await self._transcribe_aws(audio_file_path, project_id)
                
        except Exception as e:
            logger.error("Transcription failed", project_id=project_id, error=str(e))
            raise e
    
    async def _transcribe_aws(self, audio_file_path: str, project_id: str) -> Dict:
        """Use AWS Transcribe service for high-quality transcription"""
        
        job_name = f"transcribe-{project_id}-{int(datetime.now().timestamp())}"
        
        try:
            # Ensure audio file is in S3
            if not audio_file_path.startswith('s3://'):
                s3_key = f"audio-uploads/{project_id}/{os.path.basename(audio_file_path)}"
                await self._upload_to_s3(audio_file_path, s3_key)
                audio_s3_uri = f"s3://{self.bucket_name}/{s3_key}"
            else:
                audio_s3_uri = audio_file_path
            
            # Start transcription job
            response = self.transcribe.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': audio_s3_uri},
                MediaFormat=self._detect_audio_format(audio_file_path),
                LanguageCode='en-US',  # TODO: Auto-detect language
                Settings={
                    'ShowSpeakerLabels': True,
                    'MaxSpeakerLabels': 3,
                    'ShowAlternatives': True,
                    'MaxAlternatives': 2
                },
                OutputBucketName=self.bucket_name,
                OutputKey=f"transcripts/{project_id}/{job_name}.json"
            )
            
            logger.info("AWS Transcribe job started", job_name=job_name, project_id=project_id)
            
            # Poll for completion
            transcript_data = await self._poll_transcription_job(job_name, project_id)
            
            return self._format_aws_transcript(transcript_data, project_id)
            
        except ClientError as e:
            logger.error("AWS Transcribe error", error=str(e), project_id=project_id)
            # Fallback to local transcription
            return await self._transcribe_local(audio_file_path, project_id)
    
    async def _transcribe_local(self, audio_file_path: str, project_id: str) -> Dict:
        """Local transcription fallback for development/testing"""
        
        logger.info("Using local transcription fallback", project_id=project_id)
        
        try:
            # Get audio duration using pydub
            audio = AudioSegment.from_file(audio_file_path)
            duration = len(audio) / 1000.0  # Convert to seconds
            
            # Create a realistic mock transcript for development
            mock_transcript = f"This is a mock transcript for project {project_id}. " \
                            f"The audio file is approximately {duration:.1f} seconds long. " \
                            f"In production, this would be transcribed using AWS Transcribe service. " \
                            f"This mock text is useful for testing the scene generation pipeline."
            
            # Create segments (simplified segmentation)
            segments = self._create_segments_from_text(mock_transcript, duration)
            
            return {
                'transcript_id': str(uuid.uuid4()),
                'project_id': project_id,
                'full_text': mock_transcript,
                'segments': segments,
                'confidence': 0.9,  # High confidence for mock data
                'language_code': 'en-US',
                'source': 'local_mock',
                'duration': duration,
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Local transcription failed", error=str(e), project_id=project_id)
            # Return basic fallback transcript
            return {
                'transcript_id': str(uuid.uuid4()),
                'project_id': project_id,
                'full_text': "Transcription service unavailable - please add captions manually",
                'segments': [
                    {
                        'start_time': 0.0,
                        'end_time': 30.0,
                        'text': "Transcription service unavailable - please add captions manually",
                        'confidence': 0.0
                    }
                ],
                'confidence': 0.0,
                'language_code': 'en-US',
                'source': 'fallback',
                'duration': 30.0,
                'created_at': datetime.now().isoformat()
            }
    

    
    def _create_segments_from_text(self, text: str, duration: float) -> List[Dict]:
        """Create time-based segments from full text (simplified)"""
        
        # Simple word-based segmentation
        words = text.split()
        if not words:
            return []
        
        words_per_second = len(words) / duration if duration > 0 else 1
        segment_duration = min(10.0, duration / max(1, len(words) // 20))  # 10 second max segments
        
        segments = []
        current_time = 0.0
        words_per_segment = max(1, int(words_per_second * segment_duration))
        
        for i in range(0, len(words), words_per_segment):
            segment_words = words[i:i + words_per_segment]
            segment_text = ' '.join(segment_words)
            
            end_time = min(current_time + segment_duration, duration)
            
            segments.append({
                'start_time': current_time,
                'end_time': end_time,
                'text': segment_text,
                'confidence': 0.8  # Default confidence for local transcription
            })
            
            current_time = end_time
            
            if current_time >= duration:
                break
        
        return segments
    
    async def _poll_transcription_job(self, job_name: str, project_id: str, max_wait_time: int = 300) -> Dict:
        """Poll AWS Transcribe job until completion"""
        
        start_time = datetime.now()
        
        while True:
            try:
                response = self.transcribe.get_transcription_job(TranscriptionJobName=job_name)
                status = response['TranscriptionJob']['TranscriptionJobStatus']
                
                if status == 'COMPLETED':
                    # Download transcript from S3
                    transcript_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
                    return await self._download_aws_transcript(transcript_uri, project_id)
                    
                elif status == 'FAILED':
                    failure_reason = response['TranscriptionJob'].get('FailureReason', 'Unknown error')
                    raise Exception(f"AWS Transcribe job failed: {failure_reason}")
                
                # Check timeout
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > max_wait_time:
                    raise Exception(f"Transcription job timeout after {max_wait_time} seconds")
                
                # Wait before next poll
                await asyncio.sleep(5)
                
            except ClientError as e:
                logger.error("Error polling transcription job", error=str(e), job_name=job_name)
                raise e
    
    async def _download_aws_transcript(self, transcript_uri: str, project_id: str) -> Dict:
        """Download and parse AWS Transcribe result"""
        
        try:
            # Extract S3 key from URI
            s3_key = transcript_uri.split(f"{self.bucket_name}/")[1]
            
            # Download transcript
            response = self.s3.get_object(Bucket=self.bucket_name, Key=s3_key)
            transcript_data = json.loads(response['Body'].read())
            
            return transcript_data
            
        except Exception as e:
            logger.error("Failed to download AWS transcript", error=str(e), project_id=project_id)
            raise e
    
    def _format_aws_transcript(self, aws_transcript: Dict, project_id: str) -> Dict:
        """Format AWS Transcribe result to our standard format"""
        
        try:
            results = aws_transcript['results']
            
            # Extract full transcript
            full_text = results['transcripts'][0]['transcript']
            
            # Extract segments with timestamps
            segments = []
            for item in results['items']:
                if item['type'] == 'pronunciation':
                    start_time = float(item['start_time'])
                    end_time = float(item['end_time'])
                    word = item['alternatives'][0]['content']
                    confidence = float(item['alternatives'][0]['confidence'])
                    
                    # Group words into segments (every ~5 seconds)
                    # This is simplified - real implementation would be more sophisticated
                    segments.append({
                        'start_time': start_time,
                        'end_time': end_time,
                        'text': word,
                        'confidence': confidence
                    })
            
            # Group individual words into meaningful segments
            grouped_segments = self._group_words_into_segments(segments)
            
            return {
                'transcript_id': str(uuid.uuid4()),
                'project_id': project_id,
                'full_text': full_text,
                'segments': grouped_segments,
                'confidence': sum(s['confidence'] for s in segments) / len(segments) if segments else 0.0,
                'language_code': 'en-US',
                'source': 'aws_transcribe',
                'created_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to format AWS transcript", error=str(e), project_id=project_id)
            raise e
    
    def _group_words_into_segments(self, word_segments: List[Dict], max_segment_duration: float = 8.0) -> List[Dict]:
        """Group individual words into logical segments"""
        
        if not word_segments:
            return []
        
        grouped_segments = []
        current_segment_words = []
        current_segment_start = word_segments[0]['start_time']
        
        for word_data in word_segments:
            current_segment_words.append(word_data)
            
            # Check if we should end this segment
            segment_duration = word_data['end_time'] - current_segment_start
            
            if (segment_duration >= max_segment_duration or 
                word_data['text'].endswith('.') or 
                word_data['text'].endswith('!') or 
                word_data['text'].endswith('?')):
                
                # Create segment
                segment_text = ' '.join(w['text'] for w in current_segment_words)
                avg_confidence = sum(w['confidence'] for w in current_segment_words) / len(current_segment_words)
                
                grouped_segments.append({
                    'start_time': current_segment_start,
                    'end_time': word_data['end_time'],
                    'text': segment_text,
                    'confidence': avg_confidence
                })
                
                # Reset for next segment
                current_segment_words = []
                if word_segments.index(word_data) < len(word_segments) - 1:
                    current_segment_start = word_segments[word_segments.index(word_data) + 1]['start_time']
        
        # Handle remaining words
        if current_segment_words:
            segment_text = ' '.join(w['text'] for w in current_segment_words)
            avg_confidence = sum(w['confidence'] for w in current_segment_words) / len(current_segment_words)
            
            grouped_segments.append({
                'start_time': current_segment_start,
                'end_time': current_segment_words[-1]['end_time'],
                'text': segment_text,
                'confidence': avg_confidence
            })
        
        return grouped_segments
    
    def _detect_audio_format(self, file_path: str) -> str:
        """Detect audio format from file extension"""
        
        extension = os.path.splitext(file_path)[1].lower().replace('.', '')
        
        format_mapping = {
            'mp3': 'mp3',
            'wav': 'wav',
            'm4a': 'm4a',
            'aac': 'mp3',  # AWS Transcribe treats AAC as MP3
            'ogg': 'ogg',
            'flac': 'flac'
        }
        
        return format_mapping.get(extension, 'mp3')
    
    async def _upload_to_s3(self, local_path: str, s3_key: str) -> str:
        """Upload file to S3 and return the S3 URI"""
        
        try:
            with open(local_path, 'rb') as file:
                self.s3.upload_fileobj(file, self.bucket_name, s3_key)
            
            return f"s3://{self.bucket_name}/{s3_key}"
            
        except Exception as e:
            logger.error("S3 upload failed", error=str(e), s3_key=s3_key)
            raise e
    
    async def _can_use_aws_transcribe(self) -> bool:
        """Check if AWS Transcribe service is available"""
        
        try:
            # Simple check to see if we can access the service
            self.transcribe.list_transcription_jobs(MaxResults=1)
            return True
        except Exception:
            return False 