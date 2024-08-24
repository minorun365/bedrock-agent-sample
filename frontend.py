# Pyhton外部モジュールのインポート
import uuid, boto3, dotenv, os
import streamlit as st

# 環境変数からエージェントIDを取得
dotenv.load_dotenv()
AGENT_ID = os.getenv("AGENT_ID")
AGENT_ALIAS_ID = os.getenv("AGENT_ALIAS_ID")

# タイトル
st.title("スライド作ってメールで送るマン")

# Bedrock Agent Runtime クライアント
if "client" not in st.session_state:
    st.session_state.client = boto3.client("bedrock-agent-runtime")
client = st.session_state.client

# セッションID
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
session_id = st.session_state.session_id

# メッセージ
if "messages" not in st.session_state:
    st.session_state.messages = []
messages = st.session_state.messages

# 過去のメッセージを表示
for message in messages:
    with st.chat_message(message['role']):
        st.markdown(message['text'])


# チャット入力欄を定義
if prompt := st.chat_input("例：KDDIの歴史をスライドにまとめてメールで送って"):
    # ユーザーの入力をメッセージに追加
    messages.append({"role": "human", "text": prompt})

    # ユーザーの入力を画面に表示
    with st.chat_message("user"):
        st.markdown(prompt)

    response = client.invoke_agent(
        agentId=AGENT_ID,
        agentAliasId=AGENT_ALIAS_ID,
        sessionId=session_id,
        enableTrace=True,
        inputText=prompt,
    )

    # エージェントの回答を画面に表示
    with st.chat_message("assistant"):
        for event in response.get("completion"):
            # エージェントの処理状況が更新されたら画面に表示
            if "trace" in event:
                if "orchestrationTrace" in event["trace"]["trace"]:
                    orchestrationTrace = event["trace"]["trace"]["orchestrationTrace"]

                    if "modelInvocationInput" in orchestrationTrace:
                        with st.expander("思考中…", expanded=False):
                            st.write(orchestrationTrace)

                    if "rationale" in orchestrationTrace:
                        with st.expander("次のアクションを決定しました", expanded=False):
                            st.write(orchestrationTrace)

                    if "invocationInput" in orchestrationTrace:
                        with st.expander("次のタスクへのインプットを生成しました", expanded=False):
                            st.write(orchestrationTrace)

                    if "observation" in orchestrationTrace:
                        with st.expander("タスクの結果から洞察を得ています…", expanded=False):
                            st.write(orchestrationTrace)

            # エージェントの回答が出力されたら画面に表示
            if "chunk" in event:
                chunk = event["chunk"]
                answer = chunk["bytes"].decode()

                st.write(answer)
                messages.append({"role": "assistant", "text": answer})