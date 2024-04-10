import os.path
import time

import streamlit as st

st.set_page_config(
    page_title="DanceGLM",
    page_icon=":robot:",
    layout='centered',
    initial_sidebar_state='expanded',
)
from demo_user import register, database_init, login
import demo_chat, demo_tool
from enum import Enum

DATABASE = "/home/cq/code/2024/ChatGLM3/composite_demo/config/database/user.db"
database = DATABASE
DEFAULT_SYSTEM_PROMPT = '''
测试用例：
生成“天下”对应的舞蹈
生成“答案”对应的舞蹈
第一次输入：下载歌曲“喜欢你”；然后第二次输入：生成对应的舞蹈
“王利发”这一人物形象出自白话剧 ( ) A.《雷雨》 B.《北京人》 C.《天下第一楼》 D.《茶馆》
'''.strip()
# Set the title of the demo
st.title("DanceGLM 舞蹈教学")

# Add your custom text here, with smaller font size
st.markdown(
    "<sub>DanceGLM git仓库链接: https://github.com/sunny-horse-id/DanceGLM.git </sub>",
    unsafe_allow_html=True)


class Mode(str, Enum):
    CHAT, TOOL = '💬 知识问答', '🛠️ 舞蹈生成'


database_init(database)
with st.sidebar:
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = None
    print("st.session_state", st.session_state)
    options = ["注册", "登录", "状态查看"]
    page = st.selectbox('还没有账号？注册,登录', options)
    if page == "注册":
        register()
    elif page == "登录":
        st.session_state["user_id"] = login()
    else:
        if isinstance(st.session_state["user_id"], int):
            st.write("已登录,当前id:{}".format(st.session_state["user_id"]))
        else:
            st.write("当前id未登录，请先登录")
    uploaded_files = st.file_uploader("上传自定义音频,仅限tool工具调用", type=["mp3", "wav"], help="此处上传音频文件",
                                      accept_multiple_files=True, label_visibility="hidden")

    for uploaded_file in uploaded_files:
        if isinstance(st.session_state["user_id"], int):
            if uploaded_file is not None:
                # 将文件保存到本地
                with open("vue/frontend/person_music/" + str(
                        st.session_state["user_id"]) + "/music/" + uploaded_file.name,
                          "wb") as file:
                    file.write(uploaded_file.getbuffer(), )
                st.success('File {} saved!'.format(uploaded_file.name))
            else:
                st.info('Upload a file {} to save it.'.format(uploaded_file))
        else:
            st.info('检查登录状态，当前登录id{}'.format(st.session_state["user_id"]))
            uploaded_files.clear()
    top_p = st.slider(
        'top_p', 0.0, 1.0, 0.8, step=0.01
    )
    temperature = st.slider(
        'temperature', 0.0, 1.5, 0.95, step=0.01
    )
    repetition_penalty = st.slider(
        'repetition_penalty', 0.0, 2.0, 1.1, step=0.01
    )
    max_new_token = st.slider(
        'Output length', 5, 32000, 4096, step=1
    )

    cols = st.columns(2)
    export_btn = cols[0]
    clear_history = cols[1].button("Clear History", use_container_width=True)
    retry = export_btn.button("Retry", use_container_width=True)


    system_prompt = st.text_area(
        label="System Prompt (Only for chat mode)",
        height=300,
        value=DEFAULT_SYSTEM_PROMPT,
    )

prompt_text = st.chat_input(
    '和ChatGLM3聊天!',
    key='chat_input',
)

tab = st.radio(
    'Mode',
    [mode.value for mode in Mode],
    horizontal=True,
    label_visibility='hidden',
)

if clear_history or retry:
    prompt_text = ""

match tab:
    case Mode.CHAT:
        demo_chat.main(
            retry=retry,
            top_p=top_p,
            temperature=temperature,
            prompt_text=prompt_text,
            system_prompt=system_prompt,
            repetition_penalty=repetition_penalty,
            max_new_tokens=max_new_token
        )
    case Mode.TOOL:
        demo_tool.main(
            retry=retry,
            top_p=top_p,
            temperature=temperature,
            prompt_text=prompt_text,
            repetition_penalty=repetition_penalty,
            max_new_tokens=max_new_token,
            truncate_length=1024,
            user_id=st.session_state.user_id
        )
    case _:
        st.error(f'Unexpected tab: {tab}')
