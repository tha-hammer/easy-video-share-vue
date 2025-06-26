"""
Scene Generation Service
Uses LLM to generate scene beats for short-form video creation
"""

import json
import uuid
from typing import Dict, List, Optional
from datetime import datetime
import openai
import structlog

logger = structlog.get_logger(__name__)

class SceneGeneratorService:
    """Service for generating scene beats using LLM based on audio transcript"""
    
    def __init__(self, api_keys: Dict[str, str]):
        self.openai_api_key = api_keys.get('openai_api_key')
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
            self.client = openai.OpenAI(api_key=self.openai_api_key)
        else:
            logger.warning("OpenAI API key not provided, using mock generation")
            self.client = None
    
    async def generate_scene_beats(self, transcript_data: Dict, target_duration: int = 45) -> Dict:
        """
        Generate scene beats for short-form video based on transcript
        
        Args:
            transcript_data: Transcript with segments and timing
            target_duration: Target video duration in seconds (30-60)
            
        Returns:
            Dict containing scene plan with beats for video generation
        """
        
        project_id = transcript_data['project_id']
        
        logger.info("Generating scene beats", 
                   project_id=project_id, 
                   target_duration=target_duration,
                   transcript_length=len(transcript_data.get('full_text', '')))
        
        try:
            if self.client and self.openai_api_key:
                return await self._generate_with_openai(transcript_data, target_duration)
            else:
                return await self._generate_mock_scenes(transcript_data, target_duration)
                
        except Exception as e:
            logger.error("Scene generation failed", project_id=project_id, error=str(e))
            # Fallback to mock generation
            return await self._generate_mock_scenes(transcript_data, target_duration)
    
    async def _generate_with_openai(self, transcript_data: Dict, target_duration: int) -> Dict:
        """Generate scene beats using OpenAI GPT-4"""
        
        project_id = transcript_data['project_id']
        
        # Prepare transcript for LLM
        formatted_transcript = self._format_transcript_for_llm(transcript_data)
        
        prompt = self._create_scene_generation_prompt(formatted_transcript, target_duration)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                response_format={"type": "json_object"},
                max_tokens=2500
            )
            
            scene_plan = json.loads(response.choices[0].message.content)
            
            # Validate and enhance the scene plan
            validated_plan = self._validate_and_enhance_scene_plan(scene_plan, transcript_data, target_duration)
            
            logger.info("OpenAI scene generation completed", 
                       project_id=project_id,
                       scenes_count=len(validated_plan['scenes']))
            
            return validated_plan
            
        except Exception as e:
            logger.error("OpenAI generation failed", project_id=project_id, error=str(e))
            raise e
    
    async def _generate_mock_scenes(self, transcript_data: Dict, target_duration: int) -> Dict:
        """Generate mock scene beats for testing when API is unavailable"""
        
        project_id = transcript_data['project_id']
        full_text = transcript_data.get('full_text', 'Sample audio content')
        
        logger.info("Generating mock scene beats", project_id=project_id)
        
        # Create 3-4 scenes for the target duration
        scenes_count = min(4, max(3, target_duration // 12))
        scene_duration = target_duration / scenes_count
        
        scenes = []
        for i in range(scenes_count):
            start_time = i * scene_duration
            end_time = (i + 1) * scene_duration
            
            # Select portion of transcript for this scene
            segments = transcript_data.get('segments', [])
            scene_text = self._extract_text_for_timeframe(segments, start_time, end_time)
            
            if not scene_text:
                scene_text = f"Scene {i+1} content from audio"
            
            scenes.append({
                'sequence': i + 1,
                'start_time': start_time,
                'end_time': end_time,
                'duration': scene_duration,
                'audio_segment': scene_text,
                'scene_description': f"Visual scene {i+1} showing engaging content related to: {scene_text[:100]}...",
                'kling_prompt': self._create_mock_kling_prompt(scene_text, i),
                'asset_type': 'video' if i % 2 == 0 else 'image',  # Alternate video/image
                'transition_style': 'fade',
                'beat_id': str(uuid.uuid4())
            })
        
        return {
            'overall_theme': 'Professional short-form video with engaging visuals',
            'total_duration': target_duration,
            'selected_audio_segments': [
                {
                    'start_time': 0,
                    'end_time': target_duration,
                    'text': full_text[:200] + '...' if len(full_text) > 200 else full_text
                }
            ],
            'scenes': scenes,
            'caption_style': 'Bold white text with black outline, positioned in lower third',
            'target_audience': 'Instagram Reels / YouTube Shorts viewers',
            'engagement_hooks': ['Opening hook', 'Visual transitions', 'Call to action'],
            'created_at': datetime.now().isoformat(),
            'source': 'mock_generation'
        }
    
    def _create_scene_generation_prompt(self, transcript: str, target_duration: int) -> str:
        """Create the prompt for LLM scene generation"""
        
        return f"""
Create a {target_duration}-second vertical short-form video plan optimized for Instagram Reels and YouTube Shorts.

TRANSCRIPT WITH TIMESTAMPS:
{transcript}

REQUIREMENTS:
- Exactly {target_duration} seconds total duration
- 3-5 dynamic visual scenes that keep viewers engaged
- Each scene 8-15 seconds long
- Mix of video and image generation for variety
- Select the most engaging audio segments that tell a complete story
- Optimize for vertical 9:16 format and mobile viewing
- Create smooth narrative flow between scenes
- Focus on the most interesting/valuable parts of the audio

SCENE TYPES:
- "video": For dynamic action, movement, or complex scenes (use for 60-70% of scenes)
- "image": For portraits, landscapes, static concepts, or text overlays (use for 30-40% of scenes)

VISUAL STYLE GUIDELINES:
- High-quality, professional cinematography
- Consistent visual theme throughout
- Avoid copyrighted content or real people
- Use descriptive, specific prompts for AI generation
- Consider lighting, composition, and color palette
- Make visuals engaging and attention-grabbing

KLING AI PROMPT OPTIMIZATION:
- Keep prompts under 200 characters
- Be specific about visual elements
- Include style descriptors (cinematic, realistic, etc.)
- Mention lighting and composition
- Avoid complex or abstract concepts

OUTPUT FORMAT (JSON):
{{
  "overall_theme": "Brief description of the video's visual theme and mood",
  "total_duration": {target_duration},
  "selected_audio_segments": [
    {{
      "start_time": 12.5,
      "end_time": 25.0,
      "text": "Selected transcript portion that will be used"
    }}
  ],
  "scenes": [
    {{
      "sequence": 1,
      "start_time": 0,
      "end_time": 12,
      "duration": 12,
      "audio_segment": "Exact text from transcript to sync with this scene",
      "scene_description": "Detailed description of what should be shown",
      "kling_prompt": "Optimized prompt for Kling AI generation (max 200 chars)",
      "asset_type": "video",
      "transition_style": "fade",
      "visual_notes": "Additional notes about composition, lighting, mood"
    }}
  ],
  "caption_style": "Description of how captions should be styled",
  "target_audience": "Instagram Reels / YouTube Shorts viewers",
  "engagement_hooks": ["Key moments designed to maintain attention"]
}}

Ensure the scene prompts are specific, creative, and optimized for AI video/image generation.
Focus on creating a cohesive visual story that complements the audio content.
"""
    
    def _format_transcript_for_llm(self, transcript_data: Dict) -> str:
        """Format transcript with timestamps for LLM processing"""
        
        segments = transcript_data.get('segments', [])
        if not segments:
            return f"[0.0s - 30.0s]: {transcript_data.get('full_text', 'No transcript available')}"
        
        formatted_segments = []
        for segment in segments:
            start_time = segment.get('start_time', 0)
            end_time = segment.get('end_time', 30)
            text = segment.get('text', '').strip()
            
            if text:
                formatted_segments.append(f"[{start_time:.1f}s - {end_time:.1f}s]: {text}")
        
        return "\n".join(formatted_segments)
    
    def _validate_and_enhance_scene_plan(self, scene_plan: Dict, transcript_data: Dict, target_duration: int) -> Dict:
        """Validate LLM output and enhance prompts for Kling AI"""
        
        # Ensure we have required fields
        if 'scenes' not in scene_plan:
            raise ValueError("Scene plan missing 'scenes' field")
        
        # Validate total duration
        total_scene_duration = sum(scene.get('duration', 0) for scene in scene_plan['scenes'])
        if abs(total_scene_duration - target_duration) > 3:
            logger.warning("Scene duration mismatch", 
                         target=target_duration, 
                         actual=total_scene_duration)
        
        # Enhance each scene
        for i, scene in enumerate(scene_plan['scenes']):
            # Add beat_id if missing
            if 'beat_id' not in scene:
                scene['beat_id'] = str(uuid.uuid4())
            
            # Enhance Kling prompt
            if 'kling_prompt' in scene:
                scene['kling_prompt'] = self._enhance_kling_prompt(
                    scene['kling_prompt'], 
                    scene.get('asset_type', 'video')
                )
            
            # Ensure required fields
            scene['sequence'] = scene.get('sequence', i + 1)
            scene['transition_style'] = scene.get('transition_style', 'fade')
            scene['asset_type'] = scene.get('asset_type', 'video' if i % 2 == 0 else 'image')
        
        # Add metadata
        scene_plan['project_id'] = transcript_data['project_id']
        scene_plan['created_at'] = datetime.now().isoformat()
        scene_plan['source'] = 'openai_gpt4'
        
        return scene_plan
    
    def _enhance_kling_prompt(self, prompt: str, asset_type: str) -> str:
        """Enhance prompts with Kling-specific optimization"""
        
        # Add technical specifications for Kling AI
        if asset_type == "video":
            technical_suffix = " | 4K quality, smooth motion, cinematic lighting, vertical 9:16 aspect ratio"
        else:  # image
            technical_suffix = " | High resolution, professional photography, vertical composition, detailed"
        
        # Ensure prompt isn't too long for Kling API
        max_length = 200 - len(technical_suffix)
        if len(prompt) > max_length:
            prompt = prompt[:max_length-3] + "..."
        
        return prompt + technical_suffix
    
    def _extract_text_for_timeframe(self, segments: List[Dict], start_time: float, end_time: float) -> str:
        """Extract transcript text for a specific timeframe"""
        
        relevant_text = []
        
        for segment in segments:
            seg_start = segment.get('start_time', 0)
            seg_end = segment.get('end_time', 0)
            
            # Check if segment overlaps with our timeframe
            if seg_start < end_time and seg_end > start_time:
                relevant_text.append(segment.get('text', ''))
        
        return ' '.join(relevant_text).strip()
    
    def _create_mock_kling_prompt(self, scene_text: str, scene_index: int) -> str:
        """Create a mock Kling prompt based on scene text"""
        
        # Simple keyword-based prompt generation
        keywords = scene_text.lower().split()
        
        prompts = [
            "Professional office environment with natural lighting | 4K quality, cinematic",
            "Modern workspace with technology and innovation | High resolution, detailed",
            "Creative studio with artistic elements | Smooth motion, vertical composition",
            "Urban cityscape with dynamic energy | Professional photography, engaging",
            "Natural landscape with serene atmosphere | 4K quality, beautiful lighting"
        ]
        
        return prompts[scene_index % len(prompts)] 