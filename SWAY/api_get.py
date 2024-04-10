# -*- coding: utf-8 -*-
import argparse
import glob
import json
import os
import random
import sys
import wave
from functools import cmp_to_key
from pathlib import Path
from tempfile import TemporaryDirectory

import audioread
import numpy as np
import torch
import uvicorn
from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel
from starlette.responses import FileResponse
from tqdm import tqdm

from SWAY import SWAY
from SMPL_to_FBX.FbxReadWriter import FbxReadWrite
from SMPL_to_FBX.SmplObject import SmplObjects
from args import parse_test_opt
from data.audio_extraction.baseline_features import extract as baseline_extract
from data.audio_extraction.jukebox_features import extract as juke_extract
from data.slice import slice_audio

sys.path.append('.')

# app = Flask(__name__)
app = FastAPI()

display_list = []
handled_list = []

key_func = lambda x: int(os.path.splitext(x)[0].split("_")[-1].split("slice")[-1])

def stringintcmp_(a, b):
    aa, bb = "".join(a.split("_")[:-1]), "".join(b.split("_")[:-1])
    ka, kb = key_func(a), key_func(b)
    if aa < bb:
        return -1
    if aa > bb:
        return 1
    if ka < kb:
        return -1
    if ka > kb:
        return 1
    return 0

stringintkey = cmp_to_key(stringintcmp_)

def getArg():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", type=str, default="files/pkl")
    parser.add_argument(
        "--fbx_source_path",
        type=str,
        default="ybot.fbx",
    )
    parser.add_argument("--output_dir", type=str, default="files/fbx")

    return parser.parse_args()

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(NpEncoder, self).default(obj)


def convert_to_wav(music_file):
    with audioread.audio_open(music_file) as mp3:
        # 获取MP3音频参数
        channels = mp3.channels
        sample_rate = mp3.samplerate
        bits_per_sample = 16  # 因为WAV文件通常使用16位采样
        # 创建WAV文件
        with wave.open(music_file[:-4] + '.wav', 'wb') as wav:
            wav.setnchannels(channels)
            wav.setsampwidth(bits_per_sample // 8)
            wav.setframerate(sample_rate)
            # 逐块读取MP3并写入WAV文件
            for buf in mp3:
                wav.writeframes(buf)


def Generate(opt, fbx_path, music_path, pkl_path):
    feature_func = juke_extract if opt.feature_type == "jukebox" else baseline_extract
    sample_length = opt.out_length
    sample_size = int(sample_length / 2.5) - 1

    temp_dir_list = []
    all_cond = []
    all_filenames = []
    display_list.clear()

    print("Computing features for input music")

    for wav_file in glob.glob(os.path.join(music_path, "*.mp3")):
        convert_to_wav(wav_file)
        print("mp3 file name: ", wav_file)

    for wav_file in glob.glob(os.path.join(music_path, "*.wav")):
        if wav_file in handled_list:
            continue

        # create temp folder (or use the cache folder if specified)
        if opt.cache_features:
            songname = os.path.splitext(os.path.basename(wav_file))[0]
            save_dir = os.path.join(opt.feature_cache_dir, songname)
            Path(save_dir).mkdir(parents=True, exist_ok=True)
            dirname = save_dir
        else:
            temp_dir = TemporaryDirectory()
            temp_dir_list.append(temp_dir)
            dirname = temp_dir.name
        # slice the audio file
        print(f"Slicing {wav_file}")
        slice_audio(wav_file, 2.5, 5.0, dirname)
        file_list = sorted(glob.glob(f"{dirname}/*.wav"), key=stringintkey)
        # randomly sample a chunk of length at most sample_size
        rand_idx = random.randint(0, len(file_list) - sample_size)
        cond_list = []
        # generate juke representations
        print(f"Computing features for {wav_file}")
        for idx, file in enumerate(tqdm(file_list)):
            # if not caching then only calculate for the interested range
            if (not opt.cache_features) and (not (rand_idx <= idx < rand_idx + sample_size)):
                continue
            # audio = jukemirlib.load_audio(file)
            # reps = jukemirlib.extract(
            #     audio, layers=[66], downsample_target_rate=30
            # )[66]
            reps, _ = feature_func(file)
            # save reps
            if opt.cache_features:
                featurename = os.path.splitext(file)[0] + ".npy"
                np.save(featurename, reps)
            # if in the random range, put it into the list of reps we want
            # to actually use for generation
            if rand_idx <= idx < rand_idx + sample_size:
                cond_list.append(reps)
        cond_list = torch.from_numpy(np.array(cond_list))
        all_cond.append(cond_list)
        all_filenames.append(file_list[rand_idx: rand_idx + sample_size])
        # all_filenames.append(file_list)

        handled_list.append(wav_file)

        parts = wav_file.split('/')
        display_list.append([fbx_path + "/" + parts[-1][:-4] + '.fbx', wav_file])

    # # 单个文件处理
    # # Assume g.file_name is the specified file in opt.music_dir
    # specified_file = os.path.join(opt.music_dir, g.file_name)
    #
    # # 检查文件是否存在
    # if os.path.exists(specified_file + '.mp3'):
    #     convert_to_wav(specified_file)  # 假设您有一个名为 convert_to_wav 的转换函数
    #     specified_file += '.wav'  # 更新文件路径
    #
    # print("specified_file", specified_file)
    #
    # # create temp folder (or use the cache folder if specified)
    # temp_dir = TemporaryDirectory()
    # temp_dir_list.append(temp_dir)
    # dirname = temp_dir.name
    #
    # # slice the audio file
    # print(f"Slicing {specified_file}")
    # slice_audio(specified_file, 2.5, 5.0, dirname)
    # file_list = sorted(glob.glob(f"{dirname}/*.wav"), key=stringintkey)
    #
    # # randomly sample a chunk of length at most sample_size
    # cond_list = []
    #
    # # generate juke representations
    # print(f"Computing features for {specified_file}")
    # for idx, file in enumerate(tqdm(file_list)):
    #     audio = jukemirlib.load_audio(file)
    #     reps = jukemirlib.extract(
    #         audio, layers=[66], downsample_target_rate=30
    #     )[66]
    #     cond_list.append(reps)
    # cond_list = torch.from_numpy(np.array(cond_list))
    # all_cond.append(cond_list)
    # all_filenames.append(file_list)

    model = SWAY(opt.feature_type, opt.checkpoint)
    model.eval()

    # directory for optionally saving the dances for eval
    fk_out = None
    if opt.save_motions:
        fk_out = pkl_path

    print("Generating dances")
    for i in range(len(all_cond)):
        data_tuple = None, all_cond[i], all_filenames[i]
        model.render_sample(
            data_tuple, "test", opt.render_dir, render_count=-1, fk_out=fk_out, render=not opt.no_render
        )

    print("Done")
    torch.cuda.empty_cache()
    for temp_dir in temp_dir_list:
        temp_dir.cleanup()


def Convert(pkl_path, fbx_path):
    args = getArg()
    input_dir = pkl_path
    output_dir = fbx_path
    fbx_source_path = args.fbx_source_path

    smplObjects = SmplObjects(input_dir)
    for pkl_name, smpl_params in tqdm(smplObjects):
        try:
            fbxReadWrite = FbxReadWrite(fbx_source_path)
            fbxReadWrite.addAnimation(pkl_name, smpl_params)
            fbxReadWrite.writeFbx(output_dir, pkl_name)
        except Exception as e:
            fbxReadWrite.destroy()
            print("An error was thrown in the FBX conversion process")
            raise e
        finally:
            fbxReadWrite.destroy()
    # convert everything in output folder from ascii to binary
    # this line can be commented out if not directly importing to Blender
    out = os.system(f"wine SMPL-to-FBX/FbxFormatConverter.exe -c {output_dir} -binary")


class InputPath(BaseModel):
    input_path: str

@app.post("/convert_path")
async def convert_path(item: InputPath):
    input_path = item.input_path
    music_path = os.path.join(input_path, "music")
    pkl_path = os.path.join(input_path, "pkl")
    fbx_path = os.path.join(input_path, "fbx")

    opt = parse_test_opt()
    Generate(opt, fbx_path, music_path, pkl_path)

    for pkl_file in glob.glob(os.path.join(pkl_path, "*.pkl")):
        file_name = os.path.basename(pkl_file)
        if file_name.startswith('test_'):
            new_file_name = file_name[len('test_'):]  # 去掉前缀
            new_pkl_file = os.path.join(pkl_path, new_file_name)
            os.rename(pkl_file, new_pkl_file)
    print("pkl name change done")

    Convert(pkl_path, fbx_path)

    # for fbx_file in glob.glob(os.path.join(fbx_path, "*.fbx")):
    #     file_name = os.path.basename(fbx_file)
    #     if file_name.startswith('test_'):
    #         new_file_name = file_name[len('test_'):]  # 去掉前缀
    #         new_fbx_file = os.path.join(fbx_path, new_file_name)
    #         os.rename(fbx_file, new_fbx_file)
    # print("fbx name change done")

    print("/convert_path POST display_list: ", display_list)

    return {
        'display_list': display_list
    }

@app.get("/address")
async def address():
    for sublist in display_list:
        for i, path in enumerate(sublist):
            # 找到"frontend/"之后的位置
            index = path.find("frontend/") + len("frontend/")
            # 提取并更新路径
            sublist[i] = path[index:]

    return display_list

@app.get('/export')
async def export(need: str = None):
    if not need:
        raise HTTPException(status_code=400, detail="Missing 'need' parameter")
    parts = need.split("/")
    file_name = parts[-1]
    file_path = need

    try:
        return FileResponse(file_path, filename=file_name, media_type='application/octet-stream')
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error occurred while exporting file")

if __name__ == '__main__':

    # api test
    # app.run(host='192.168.0.100', port=5017, debug=True)
    uvicorn.run(app, host="192.168.0.100", port=5017)
    # uvicorn.run(app, host="172.16.3.214", port=5017)

    # local test
    # opt = parse_test_opt()
    # clear_directory()
    # Generate(opt)
    # Convert()