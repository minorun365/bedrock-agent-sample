# Pyhton外部モジュールのインポート
import json, boto3, os

# SNSトピックARNを環境変数から取得
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

def lambda_handler(event, context):
    # パラメータからURLを取得
    presentation_url = event.get('parameters', [{}])[0].get('value')

    # SNSクライアントの作成
    sns = boto3.client('sns')
    
    # メッセージの作成
    message = f"Bedrockエージェントがスライドを作成しました。以下のURLからアクセスできます：\n{presentation_url}"
    
    # SNSメッセージの発行
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=message,
        Subject="スライド作成通知"
    )
    
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