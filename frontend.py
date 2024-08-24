# Pyhton外部モジュールのインポート
import uuid, boto3, dotenv, os
import streamlit as st

# 環境変数からエージェントIDを取得
dotenv.load_dotenv()
AGENT_ID = os.getenv("AGENT_ID")
AGENT_ALIAS_ID = os.getenv("AGENT_ALIAS_ID")

# タイトル
st.title("パワポ作成エージェント")

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


# チャット入力欄を定義
if prompt := st.chat_input("何でも聞いてください。"):
    # ユーザーの入力をメッセージに追加
    messages.append({"role": "human", "text": prompt})

    # ユーザーの入力を画面表示
    with st.chat_message("user"):
        st.markdown(prompt)

    response = client.invoke_agent(
        agentId=AGENT_ID,
        agentAliasId=AGENT_ALIAS_ID,
        sessionId=session_id,
        enableTrace=True,
        inputText=prompt,
        # sessionState={"files": get_files()},
    )

    with st.chat_message("assistant"):
        for event in response.get("completion"):
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
                        if (
                            "codeInterpreterInvocationInput"
                            in orchestrationTrace["invocationInput"]
                            and "code"
                            in orchestrationTrace["invocationInput"][
                                "codeInterpreterInvocationInput"
                            ]
                        ):
                            code = orchestrationTrace["invocationInput"][
                                "codeInterpreterInvocationInput"
                            ]["code"]

                            with st.expander("code", expanded=False):
                                st.write(orchestrationTrace)

                            with st.expander("Python Code", expanded=False):
                                st.markdown(f"```\n{code}\n```")
                        else:
                            with st.expander("次のタスクへのインプットを生成しました", expanded=False):
                                st.write(orchestrationTrace)

                    if "observation" in orchestrationTrace:
                        with st.expander("タスクの結果から洞察を得ています…", expanded=False):
                            st.write(orchestrationTrace)

            if "files" in event:
                files = event["files"]["files"]
                for file in files:

                    with open(file["name"], mode="wb") as f:
                        f.write(file["bytes"])

                    st.image(file["bytes"], caption=file["name"])

            if "chunk" in event:
                chunk = event["chunk"]
                answer = chunk["bytes"].decode()

                st.write(answer)
                messages.append({"role": "assistant", "text": answer})
