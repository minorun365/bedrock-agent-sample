# Python外部モジュールのインポート
import json
from duckduckgo_search import DDGS

# メインのLambda関数
def lambda_handler(event, context):
    # イベントパラメータから検索クエリを取得
    query = next(
        (item["value"] for item in event["parameters"] if item["name"] == "query"), ""
    )

    # DuckDuckGoを使用して検索を実行
    results = list(
        DDGS().text(
            keywords=query,
            region="jp-jp",  # 日本向けの検索結果を取得
            safesearch="off",  # セーフサーチをオフに設定
            timelimit=None,  # 時間制限なし
            max_results=10,  # 最大5件の結果を取得
        )
    )

    # 検索結果をフォーマット
    summary = "\n\n".join(
        [f"タイトル: {result['title']}\n要約: {result['body']}" for result in results]
    )

    # レスポンスの作成と返却
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event["actionGroup"],
            "function": event["function"],
            "functionResponse": {
                "responseBody": {
                    "TEXT": {
                        "body": json.dumps({"summary": summary}, ensure_ascii=False)
                    }
                }
            },
        },
    }