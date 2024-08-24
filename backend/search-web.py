import json
import logging
from duckduckgo_search import DDGS

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")
    
    query = next((item['value'] for item in event['parameters'] if item['name'] == 'query'), '')
    logger.info(f"Search query: {query}")
    
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(
                keywords=query,
                region='jp-jp',
                safesearch='off',
                timelimit=None,
                max_results=5
            ))
        
        logger.info(f"Search results: {json.dumps(results, ensure_ascii=False)}")
        
        if not results:
            summary = "検索結果が見つかりませんでした。"
        else:
            summary = "\n\n".join([f"タイトル: {result['title']}\n要約: {result['body']}" for result in results])
        
        return {
            'messageVersion': '1.0',
            'response': {
                'actionGroup': event['actionGroup'],
                'function': event['function'],
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps({'summary': summary}, ensure_ascii=False)
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
                'actionGroup': event['actionGroup'],
                'function': event['function'],
                'functionResponse': {
                    'responseBody': {
                        'TEXT': {
                            'body': json.dumps({'error': f"検索中にエラーが発生しました: {str(e)}"}, ensure_ascii=False)
                        }
                    }
                }
            }
        }