import shutil
from dataclasses import dataclass
from enum import auto, Enum
import json
from io import BytesIO
import zipfile
import re
import os
import tempfile

from PIL.Image import Image
import streamlit as st
from streamlit.delta_generator import DeltaGenerator

TOOL_PROMPT = 'Answer the following questions as best as you can. You have access to the following tools:\n'


class Role(Enum):
    SYSTEM = auto()
    USER = auto()
    ASSISTANT = auto()
    TOOL = auto()
    INTERPRETER = auto()
    OBSERVATION = auto()

    def __str__(self):
        match self:
            case Role.SYSTEM:
                return "<|system|>"
            case Role.USER:
                return "<|user|>"
            case Role.ASSISTANT | Role.TOOL | Role.INTERPRETER:
                return "<|assistant|>"
            case Role.OBSERVATION:
                return "<|observation|>"

    # Get the message block for the given role
    def get_message(self):
        # Compare by value here, because the enum object in the session state
        # is not the same as the enum cases here, due to streamlit's rerunning
        # behavior.
        match self.value:
            case Role.SYSTEM.value:
                return
            case Role.USER.value:
                return st.chat_message(name="user", avatar="user")
            case Role.ASSISTANT.value:
                return st.chat_message(name="assistant", avatar="assistant")
            case Role.TOOL.value:
                return st.chat_message(name="tool", avatar="assistant")
            case Role.INTERPRETER.value:
                return st.chat_message(name="interpreter", avatar="assistant")
            case Role.OBSERVATION.value:
                return st.chat_message(name="observation", avatar="user")
            case _:
                st.error(f'Unexpected role: {self}')


@dataclass
class Conversation:
    role: Role
    content: str
    tool: str | None = None
    fbx_path: str | None = None
    music: str | None = None
    files: list[[str, str]] | None = None

    def __str__(self) -> str:
        print(self.role, self.content, self.tool)
        match self.role:
            case Role.SYSTEM | Role.USER | Role.ASSISTANT | Role.OBSERVATION:
                return f'{self.role}\n{self.content}'
            case Role.TOOL:
                return f'{self.role}{self.tool}\n{self.content}'
            case Role.INTERPRETER:
                return f'{self.role}interpreter\n{self.content}'

    # Human readable format
    def get_text(self) -> str:
        text = postprocess_text(self.content)
        match self.role.value:
            case Role.TOOL.value:
                text = f'Calling tool `{self.tool}`:\n\n{text}'
            case Role.INTERPRETER.value:
                text = f'{text}'
            case Role.OBSERVATION.value:
                text = f'Observation:\n```\n{text}\n```'
        return text

    # Display as a markdown block
    def show(self, placeholder: DeltaGenerator | None = None) -> str:
        if placeholder:
            message = placeholder
        else:
            message = self.role.get_message()
        if self.files:
            fbx_file = [fbx[0] for fbx in self.files]
            parent_path, file_name = os.path.split(fbx_file[0])
            zip_path = os.path.join(parent_path, file_name.split(".")[0] + ".zip")
            wav_file = [wav[1] for wav in self.files]
            files = []
            files.extend(fbx_file)
            files.extend(wav_file)
            res = filetozip(zip_path, files)
            print(zip_path)
            if res:
                with message.container():
                    with open(zip_path, "rb") as zip_file:
                        message.download_button(
                            label="Download {}".format(file_name.split(".")[0] + ".zip"),
                            data=zip_file,
                            file_name=file_name.split(".")[0] + ".zip",
                            mime='application/stream',
                        )
        elif self.fbx_path:
            message.markdown(
                '<iframe src="http://192.168.0.100:5173" width="100%" height="400"></iframe>',
                unsafe_allow_html=True)
        elif self.music:
            print(self.music)
            parent_path, file_name = os.path.split(self.music)
            with message.container():
                with open(self.music, "rb") as music:
                    message.download_button(
                        label="Download {}".format(file_name),
                        data=music,
                        file_name=file_name,
                        mime='application/stream',
                    )
        else:
            text = self.get_text()
            message.markdown(text)


def preprocess_text(
        system: str | None,
        tools: list[dict] | None,
        history: list[Conversation],
) -> str:
    if tools:
        tools = json.dumps(tools, indent=4, ensure_ascii=False)

    prompt = f"{Role.SYSTEM}\n"
    prompt += system if not tools else TOOL_PROMPT
    if tools:
        tools = json.loads(tools)
        prompt += json.dumps(tools, ensure_ascii=False)
    for conversation in history:
        prompt += f'{conversation}'
    prompt += f'{Role.ASSISTANT}\n'
    return prompt


def postprocess_text(text: str) -> str:
    text = text.replace("\(", "$")
    text = text.replace("\)", "$")
    text = text.replace("\[", "$$")
    text = text.replace("\]", "$$")
    text = text.replace("<|assistant|>", "")
    text = text.replace("<|observation|>", "")
    text = text.replace("<|system|>", "")
    text = text.replace("<|user|>", "")
    return text.strip()


def filetozip(zip_name: str, file_path_list: list):
    """
    压缩指定文件夹
    :zip_name: 'school.zip'
    :file_path_list: ['/home/name/zhangsan.txt', '/home/name/lisi.txt']
    """
    # 创建zip文件
    try:
        zip = zipfile.ZipFile(zip_name, mode='w', compression=zipfile.ZIP_DEFLATED)
        # 文件写入
        for file in file_path_list:
            # 找到文件名
            parent_path, file_name = os.path.split(file)
            # 添加文件夹到对应目录下（name目录下）
            zip.write(file, file_name)
        zip.close()
    except:
        return False
    return True


def dirtozip(self, zip_name: str, file_path_list: list, dir_path_list: list):
    # 文件夹写入(由具体需求设计)
    # :    :dir_path_list: ['/home/grages', '/home/class']

    zip = zipfile.ZipFile(zip_name, mode='w', compression=zipfile.ZIP_DEFLATED)
    for dir in dir_path_list:
        # 当前目录
        dir_path = os.path.basename(dir)
        # dir_path = dir.split('/')[-1]
        # title = re.findall(r'/home/(.+?)/',dir)[0]
        # 上一级目录
        title = os.path.basename(os.path.dirname(dir))
        # 遍历文件
        for path, dirnames, filenames in os.walk(dir):
            # 创建多级目录，第一级(/home)
            folder = zipfile.ZipInfo(os.path.dirname(title))
            folder.external_attr = 0x10
            # 创建第二级目录(grades或class)
            folder = zipfile.ZipInfo(os.path.join(title, dir_path))
            folder.external_attr = 0x10
            # 添加文件到对应目录即（/home/grages下或/home/class下）
            for filename in filenames:
                file_path = os.path.join(path, filename)
                zip.write(file_path, os.path.join('', dir_path, filename))
