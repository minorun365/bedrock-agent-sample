import json
import os
import logging
import uuid
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        topic = next((item['value'] for item in event['parameters'] if item['name'] == 'topic'), '')
        content = next((item['value'] for item in event['parameters'] if item['name'] == 'content'), '')
        
        if not topic or not content:
            raise ValueError("Missing required parameters: topic and content")

        creds_json = json.loads(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])
        creds = service_account.Credentials.from_service_account_info(creds_json)
        
        service = build('slides', 'v1', credentials=creds)
        
        # プレゼンテーションの作成
        presentation = service.presentations().create(body={'title': topic}).execute()
        presentation_id = presentation.get('presentationId')
        logger.info(f"Created presentation with ID: {presentation_id}")

        # スライドの追加
        slides = create_slides(service, presentation_id, content)
        
        # Drive APIクライアントの作成
        drive_service = build('drive', 'v3', credentials=creds)
        
        # スライドの共有設定
        permission = {
            'type': 'anyone',
            'role': 'reader',
            'allowFileDiscovery': False
        }
        drive_service.permissions().create(
            fileId=presentation_id,
            body=permission,
            fields='id'
        ).execute()
        logger.info("Sharing permission created")
        
        # プレゼンテーションのURLを取得
        file = drive_service.files().get(fileId=presentation_id, fields='webViewLink').execute()
        web_view_link = file.get('webViewLink')
        logger.info(f"Web view link: {web_view_link}")
        
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': event.get('actionGroup', 'default'),
                'function': event['function'],
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps({
                                'message': 'Presentation created and shared successfully',
                                'presentationUrl': web_view_link
                            })
                        }
                    }
                }
            }
        }
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': event.get('actionGroup', 'default'),
                'function': event.get('function', 'default'),
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps({
                                'error': f'An error occurred: {str(e)}'
                            })
                        }
                    }
                }
            }
        }

def create_slides(service, presentation_id, content):
    slides = []
    slide_contents = content.split('\n\n')
    
    for index, slide_content in enumerate(slide_contents):
        lines = slide_content.strip().split('\n')
        title = lines[0].replace('スライド', '').strip(':')
        body = '\n'.join(lines[1:])
        
        object_id = f'slide_{uuid.uuid4().hex[:8]}'
        title_id = f'title_{uuid.uuid4().hex[:8]}'
        body_id = f'body_{uuid.uuid4().hex[:8]}'
        
        requests = [
            {
                'createSlide': {
                    'objectId': object_id,
                    'insertionIndex': str(index),
                    'slideLayoutReference': {
                        'predefinedLayout': 'TITLE_AND_BODY'
                    },
                    'placeholderIdMappings': [
                        {
                            'layoutPlaceholder': {
                                'type': 'TITLE'
                            },
                            'objectId': title_id
                        },
                        {
                            'layoutPlaceholder': {
                                'type': 'BODY'
                            },
                            'objectId': body_id
                        }
                    ]
                }
            },
            {
                'insertText': {
                    'objectId': title_id,
                    'insertionIndex': 0,
                    'text': title
                }
            },
            {
                'insertText': {
                    'objectId': body_id,
                    'insertionIndex': 0,
                    'text': body
                }
            }
        ]
        
        response = service.presentations().batchUpdate(
            presentationId=presentation_id,
            body={'requests': requests}
        ).execute()
        
        logger.info(f"Created slide {index + 1}")
        slides.append(object_id)
    
    return slides