import json
import logging
import boto3
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# SNSトピックARNを環境変数から取得
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")

    try:
        if not SNS_TOPIC_ARN:
            raise ValueError("SNS_TOPIC_ARN environment variable is not set")

        # パラメータからURLを取得
        presentation_url = event.get('parameters', [{}])[0].get('value')

        if not presentation_url:
            raise ValueError("Missing required parameter: presentation_url")

        # SNSクライアントの作成
        sns = boto3.client('sns')
        
        # メッセージの作成
        message = f"Bedrockエージェントがスライドを作成しました。以下のURLからアクセスできます：\n{presentation_url}"
        
        # SNSメッセージの発行
        response = sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=message,
            Subject="スライド作成通知"
        )
        
        logger.info(f"Notification sent successfully: {response['MessageId']}")
        
        # Bedrock Agentが期待する形式で応答を返す
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': event.get('actionGroup', 'send-email'),
                'function': event.get('function', 'send-email'),
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps({
                                'message': 'Email sent successfully',
                                'presentationUrl': presentation_url
                            })
                        }
                    }
                }
            }
        }
    
    except ValueError as ve:
        logger.error(f"ValueError: {str(ve)}")
        return format_error_response(str(ve), 400)
    except boto3.exceptions.Boto3Error as be:
        logger.error(f"Boto3Error: {str(be)}")
        return format_error_response(f"AWS service error: {str(be)}", 500)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return format_error_response(f"An unexpected error occurred: {str(e)}", 500)

def format_error_response(error_message, status_code):
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': 'send-email',
            'function': 'send-email',
            'functionResponse': {
                'responseBody': {
                    'TEXT': {
                        'body': json.dumps({
                            'error': error_message,
                            'statusCode': status_code
                        })
                    }
                }
            }
        }
    }