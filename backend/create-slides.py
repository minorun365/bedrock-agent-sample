# Pyhton外部モジュールのインポート
import json, os, uuid
from google.oauth2 import service_account
from googleapiclient.discovery import build

def lambda_handler(event, context):
    # イベントパラメータからトピックとコンテンツを取得
    topic = next(
        (item["value"] for item in event["parameters"] if item["name"] == "topic"), ""
    )
    content = next(
        (item["value"] for item in event["parameters"] if item["name"] == "content"), ""
    )

    # 環境変数からGoogle認証情報を取得し、認証オブジェクトを作成
    creds_json = json.loads(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
    creds = service_account.Credentials.from_service_account_info(creds_json)

    # Google Slides APIクライアントの作成
    service = build("slides", "v1", credentials=creds)

    # プレゼンテーションの作成
    presentation = service.presentations().create(body={"title": topic}).execute()
    presentation_id = presentation.get("presentationId")

    # スライドの追加
    create_slides(service, presentation_id, content)

    # Google Drive APIクライアントの作成
    drive_service = build("drive", "v3", credentials=creds)

    # スライドの共有設定（誰でも閲覧可能に設定）
    permission = {"type": "anyone", "role": "reader", "allowFileDiscovery": False}
    drive_service.permissions().create(
        fileId=presentation_id, body=permission, fields="id"
    ).execute()

    # プレゼンテーションの閲覧用URLを取得
    file = (
        drive_service.files()
        .get(fileId=presentation_id, fields="webViewLink")
        .execute()
    )
    web_view_link = file.get("webViewLink")

    # レスポンスの作成と返却
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", "default"),
            "function": event["function"],
            "functionResponse": {
                "responseBody": {
                    "TEXT": {
                        "body": json.dumps(
                            {
                                "message": "Presentation created and shared successfully",
                                "presentationUrl": web_view_link,
                            }
                        )
                    }
                }
            },
        },
    }

def create_slides(service, presentation_id, content):
    slides = []
    
    # コンテンツを各スライドに分割
    slide_contents = content.split("\n\n")

    # 最初のスライド（タイトルスライド）を削除
    delete_requests = [{'deleteObject': {'objectId': 'p'}}]
    service.presentations().batchUpdate(
        presentationId=presentation_id, body={'requests': delete_requests}).execute()

    for index, slide_content in enumerate(slide_contents):
        lines = slide_content.strip().split("\n")
        title = lines[0].replace("スライド", "").strip(":")
        body = "\n".join(lines[1:])

        # 各要素に一意のIDを割り当て
        object_id = f"slide_{uuid.uuid4().hex[:8]}"
        title_id = f"title_{uuid.uuid4().hex[:8]}"
        body_id = f"body_{uuid.uuid4().hex[:8]}"

        # スライドの作成とコンテンツの挿入リクエストを準備
        requests = [
            {
                "createSlide": {
                    "objectId": object_id,
                    "insertionIndex": str(index),
                    "slideLayoutReference": {"predefinedLayout": "TITLE_AND_BODY"},
                    "placeholderIdMappings": [
                        {"layoutPlaceholder": {"type": "TITLE"}, "objectId": title_id},
                        {"layoutPlaceholder": {"type": "BODY"}, "objectId": body_id},
                    ],
                }
            },
            {"insertText": {"objectId": title_id, "insertionIndex": 0, "text": title}},
            {"insertText": {"objectId": body_id, "insertionIndex": 0, "text": body}},
        ]

        # バッチ更新の実行
        response = (
            service.presentations()
            .batchUpdate(presentationId=presentation_id, body={"requests": requests})
            .execute()
        )

        slides.append(object_id)

    return slides