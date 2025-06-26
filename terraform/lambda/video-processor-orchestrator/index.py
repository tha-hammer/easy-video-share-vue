import json
import boto3
import os
import uuid
from datetime import datetime

ecs = boto3.client('ecs')
dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    """
    Lambda function to orchestrate video processing using ECS
    Triggered by API Gateway or EventBridge events
    """
    
    try:
        # Parse the incoming event
        if 'body' in event:
            # API Gateway event
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            # Direct invocation or EventBridge event
            body = event
        
        project_id = body.get('project_id')
        audio_s3_key = body.get('audio_s3_key', '')
        
        if not project_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'body': json.dumps({'error': 'project_id is required'})
            }
        
        # Update project status to processing
        projects_table = dynamodb.Table(os.environ['AI_PROJECTS_TABLE'])
        projects_table.update_item(
            Key={'project_id': project_id},
            UpdateExpression='SET #status = :status, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'processing',
                ':updated_at': datetime.now().isoformat()
            }
        )
        
        # Run ECS task for video processing
        task_response = ecs.run_task(
            cluster=os.environ['ECS_CLUSTER_ARN'],
            taskDefinition=os.environ['ECS_TASK_DEFINITION'],
            launchType='FARGATE',
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': os.environ['SUBNET_IDS'].split(','),
                    'securityGroups': [os.environ['SECURITY_GROUP_ID']],
                    'assignPublicIp': 'ENABLED'
                }
            },
            overrides={
                'containerOverrides': [
                    {
                        'name': 'video-processor',
                        'environment': [
                            {
                                'name': 'PROJECT_ID',
                                'value': project_id
                            },
                            {
                                'name': 'AUDIO_S3_KEY',
                                'value': audio_s3_key
                            }
                        ]
                    }
                ]
            },
            tags=[
                {
                    'key': 'ProjectId',
                    'value': project_id
                },
                {
                    'key': 'Environment',
                    'value': os.environ.get('ENVIRONMENT', 'dev')
                }
            ]
        )
        
        task_arn = task_response['tasks'][0]['taskArn']
        
        # Update project with task ARN
        projects_table.update_item(
            Key={'project_id': project_id},
            UpdateExpression='SET task_arn = :task_arn, updated_at = :updated_at',
            ExpressionAttributeValues={
                ':task_arn': task_arn,
                ':updated_at': datetime.now().isoformat()
            }
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps({
                'project_id': project_id,
                'task_arn': task_arn,
                'status': 'processing',
                'message': 'Video processing started'
            })
        }
        
    except Exception as e:
        print(f"Error processing video generation request: {str(e)}")
        
        # Update project status to failed if we have project_id
        if 'project_id' in locals():
            try:
                projects_table.update_item(
                    Key={'project_id': project_id},
                    UpdateExpression='SET #status = :status, error_message = :error, updated_at = :updated_at',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={
                        ':status': 'failed',
                        ':error': str(e),
                        ':updated_at': datetime.now().isoformat()
                    }
                )
            except:
                pass  # Don't fail the response if we can't update the database
        
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        } 