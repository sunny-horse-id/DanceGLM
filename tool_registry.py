"""
This code is the tool registration part. By registering the tool, the model can call the tool.
This code provides extended functionality to the model, enabling it to call and interact with a variety of utilities
through defined interfaces.
"""

import copy
import inspect
import os
import random
import time
from pprint import pformat
import traceback
from types import GenericAlias
from typing import get_origin, Annotated, Optional
import streamlit as st
import subprocess
from utils import USER_AGENT as user_agent, dir_init
import requests
import jsonpath
import os

_TOOL_HOOKS = {}
_TOOL_DESCRIPTIONS = {}


def register_tool(func: callable):
    tool_name = func.__name__
    tool_description = inspect.getdoc(func).strip()
    python_params = inspect.signature(func).parameters
    tool_params = []
    for name, param in python_params.items():
        annotation = param.annotation
        if annotation is inspect.Parameter.empty:
            raise TypeError(f"Parameter `{name}` missing type annotation")
        if get_origin(annotation) != Annotated:
            raise TypeError(f"Annotation type for `{name}` must be typing.Annotated")

        typ, (description, required) = annotation.__origin__, annotation.__metadata__
        typ: str = str(typ) if isinstance(typ, GenericAlias) else typ.__name__
        if not isinstance(description, str):
            raise TypeError(f"Description for `{name}` must be a string")
        if not isinstance(required, bool):
            raise TypeError(f"Required for `{name}` must be a bool")

        tool_params.append({
            "name": name,
            "description": description,
            "type": typ,
            "required": required
        })
    tool_def = {
        "name": tool_name,
        "description": tool_description,
        "params": tool_params
    }
    print("[registered tool] " + pformat(tool_def))
    _TOOL_HOOKS[tool_name] = func
    _TOOL_DESCRIPTIONS[tool_name] = tool_def

    return func


def dispatch_tool(tool_name: str, tool_params: dict) -> str:
    if tool_name not in _TOOL_HOOKS:
        return f"Tool `{tool_name}` not found. Please use a provided tool."
    tool_call = _TOOL_HOOKS[tool_name]
    try:
        ret = tool_call(**tool_params)
    except:
        ret = traceback.format_exc()
    return ret


def get_tools() -> dict:
    return copy.deepcopy(_TOOL_DESCRIPTIONS)


# Tool Definitions

@register_tool
def random_number_generator(
        seed: Annotated[int, 'The random seed used by the generator', True],
        range: Annotated[tuple[int, int], 'The range of the generated numbers', True],
) -> str:
    """
    Generates a random number x, s.t. range[0] <= x < range[1]
    """
    if not isinstance(seed, int):
        raise TypeError("Seed must be an integer")
    if not isinstance(range, tuple):
        raise TypeError("Range must be a tuple")
    if not isinstance(range[0], int) or not isinstance(range[1], int):
        raise TypeError("Range must be a tuple of integers")

    import random
    return str(random.Random(seed).randint(*range))


@register_tool
def get_weather(
        city_name: Annotated[str, 'The name of the city to be queried', True],
) -> str:
    """
    Get the current weather for `city_name`
    """

    if not isinstance(city_name, str):
        raise TypeError("City name must be a string")

    key_selection = {
        "current_condition": ["temp_C", "FeelsLikeC", "humidity", "weatherDesc", "observation_time"],
    }
    import requests
    try:
        resp = requests.get(f"https://wttr.in/{city_name}?format=j1")
        resp.raise_for_status()
        resp = resp.json()
        ret = {k: {_v: resp[k][0][_v] for _v in v} for k, v in key_selection.items()}
    except:
        import traceback
        ret = "Error encountered while fetching weather data!\n" + traceback.format_exc()

    return str(ret)


@register_tool
def get_current_location(

) -> str:
    """
    Get the current location
    """
    locations = ["长沙", "武汉", "广州", "深圳", "上海"]
    print(locations, st.session_state.user_id)

    return random.choice(locations)


@register_tool
def get_shell(
        query: Annotated[str, 'The command should run in Linux shell', True],
) -> str:
    """
       Use shell to run command
    """
    if not isinstance(query, str):
        raise TypeError("Command must be a string")
    try:
        result = subprocess.run(query, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return e.stderr


@register_tool
def get_music(
        music_name: Annotated[str, 'The name of the music to be queried for generating dacne', True],
) -> str:
    """
    使用音乐名搜索歌曲并下载
    use the 'music_name' to search in the website and download it
    """
    music_platform = ["netease", "qq", "kugou", "kuwo", "baidu", "ximalaya"]
    try:
        personal_id = st.session_state.user_id
    except:
        personal_id = 0
        dir_init(personal_id)
    if not music_name:
        music_name = "天下"

    print("1.网易云:netease\n2.QQ:qq\n3.酷狗:kugou\n4.酷我:kuwo\n5.百度:baidu\n6.喜马拉雅:ximalaya")

    print("-------------------------------------------------------")
    url = 'https://music.liuzhijin.cn/'

    res = ""
    path = ""
    for platform in music_platform:
        headers = {
            "user-agent": random.choice(user_agent),
            # 判断请求是异步还是同步
            "x-requested-with": "XMLHttpRequest",
        }
        param = {
            "input": music_name,
            "filter": "name",
            "type": platform,
            "page": 1,
        }
        try:
            res = requests.post(url=url, data=param, headers=headers)
        except:
            print("{}获取失败".format(music_name))
            continue
        json_text = res.json()

        title = jsonpath.jsonpath(json_text, '$..title')
        print("title", title)
        author = jsonpath.jsonpath(json_text, '$..author')
        url = jsonpath.jsonpath(json_text, '$..url')
        if title:
            path = song_download_for_music(url[0], title[0], author[0], personal_id=personal_id)
            if path:
                print(path)
                break
        else:
            print("对不起，{}暂无搜索结果!正在搜索下一个".format(platform))
            res = "对不起，{}暂无搜索结果!可能是版权受限或者网络问题，请重新尝试。".format(music_name)
    print(res)
    return path


@register_tool
def get_dance(
        music: Annotated[str, 'The name of the music to be queried for generating dacne', True],
) -> list | str:
    """
    Get the special dance for `music_name`
    """
    res = ""
    ret = res
    if isinstance(st.session_state.user_id, int):
        input_path = "vue/frontend/person_music/" + str(st.session_state.user_id)
        input_path = os.path.abspath(input_path)
    else:
        ret += "舞蹈视频生成错误，请联系开发人员\n"
        return ret
    if not isinstance(music, str):
        raise TypeError("音乐必须是一个可以被解读的文字")
    if "上传" not in music:
        res = get_music_downloads(music, st.session_state.user_id)
    if "暂无搜索结果" in res:
        get_music_downloads(None, st.session_state.user_id)
        res = "已替换歌曲:白月光与朱砂痣"
        print(res)

    try:
        resp = requests.post("http://192.168.0.100:5017/convert_path", json={'input_path': input_path})
        resp = resp.json()
        # fbx_path = resp["fbx_path"]
        display_list = resp["display_list"]
        # display_list = [["vue/frontend/person_music/1/fbx/test_Can't Wait to Be with You.fbx",
        #                  "vue/frontend/person_music/1/music/Can't Wait to Be with You.wav"]]

        # music_path = resp["music_path"]
        # while not len(final_file_list):
        #     time.sleep(5)  # sixty second delay
        #     try:
        #         requests.get()
        #         break
        #     except:
        #         print("File not ready, trying again in five seconds")
        print("display_list:", display_list)
        # print("fbx_path:", fbx_path)
        # print("music_path", music_path)
        # ret += "[舞蹈视频]({}) \n".format(resp)
        return display_list
    except:
        import traceback
        ret = [ret + " 舞蹈视频生成错误，请联系开发人员\n" + traceback.format_exc()]

    # TODO 拿到fbx文件后发送路径至播放器

    return ret


"""
  1.url
  2.模拟浏览器请求
  3.解析网页源代码
  4.保存数据
"""


def song_download(url, title, author, personal_id):
    # 创建文件夹
    # os.makedirs("music", exist_ok=True)
    path = 'vue/frontend/person_music/{}/music/{}.mp3'.format(personal_id, title)
    print('歌曲:{0}-{1},正在下载...'.format(title, author))
    # 下载（这种读写文件的下载方式适合少量文件的下载）
    content = requests.get(url).content
    # with open(file=title + author + '.mp3', mode='wb') as f:
    with open(file=path, mode='wb') as f:
        f.write(content)
    print('下载完毕,{0}-{1}'.format(title, author))
    return '下载完毕,{0}-{1}'.format(title, author)


def song_download_for_music(url, title, author, personal_id):
    # 创建文件夹
    # os.makedirs("music", exist_ok=True)
    path = 'vue/frontend/person_music/{}/music/{}.mp3'.format(personal_id, title)
    path = os.path.abspath(path)
    print('歌曲:{0}-{1},正在下载...'.format(title, author))
    # 下载（这种读写文件的下载方式适合少量文件的下载）
    content = requests.get(url).content
    # with open(file=title + author + '.mp3', mode='wb') as f:
    with open(file=path, mode='wb') as f:
        f.write(content)
    print('下载完毕,{0}-{1}'.format(title, author))
    return path


def get_music_downloads(name: Optional[str], user_id: Optional[int]):
    """
    搜索歌曲名称
    :return:
    """
    music_platform = ["netease", "qq", "kugou", "kuwo", "baidu", "ximalaya"]
    # try:
    #     personal_id = st.session_state.user_id
    # except:
    #     print("error")
    # finally:
    #     personal_id = 1
    try:
        personal_id = st.session_state.user_id
    except:
        personal_id = user_id
    if not name:
        name = "白月光与朱砂痣"

    print("1.网易云:netease\n2.QQ:qq\n3.酷狗:kugou\n4.酷我:kuwo\n5.百度:baidu\n6.喜马拉雅:ximalaya")

    print("-------------------------------------------------------")
    url = 'https://music.liuzhijin.cn/'

    res = ""
    for platform in music_platform:
        headers = {
            "user-agent": random.choice(user_agent),
            # 判断请求是异步还是同步
            "x-requested-with": "XMLHttpRequest",
        }
        param = {
            "input": name,
            "filter": "name",
            "type": platform,
            "page": 1,
        }
        try:
            res = requests.post(url=url, data=param, headers=headers)
        except:
            print("{}获取失败".format(name))
            continue
        json_text = res.json()

        title = jsonpath.jsonpath(json_text, '$..title')
        print("title", title)
        author = jsonpath.jsonpath(json_text, '$..author')
        url = jsonpath.jsonpath(json_text, '$..url')
        if title:
            res = song_download(url[0], title[0], author[0], personal_id=personal_id)
            if "下载完毕" in res:
                res = "下载完毕"
                break
        else:
            print("对不起，{}暂无搜索结果!正在搜索下一个".format(platform))
            res = "对不起，{}暂无搜索结果!可能是版权受限或者网络问题，请重新尝试。".format(name)
    return res


if __name__ == "__main__":
    # print(dispatch_tool("get_shell", {"query": "pwd"}))
    # print(dispatch_tool("get_dance", {"music": "爱人错过"}))
    # print(get_tools())
    music_name = "答案"
    get_music_downloads(music_name, 1)
