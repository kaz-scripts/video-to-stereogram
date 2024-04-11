import numpy as np
from PIL import Image
import cv2
import os
import ffmpeg
import glob
import tqdm
import subprocess
from multiprocessing import Pool

#動画から音声を抽出
def extract_audio(video_path, output):
    stream = ffmpeg.input(video_path, hwaccel='cuda')
    stream = ffmpeg.output(stream,'bgm.mp3')
    ffmpeg.run(stream)

#画像と抽出した音声を連結して出力(ffmpegの実行ファイルが必要)
def merge_imgs(folder_path, audio_path, output, fps):
    images = sorted([img for img in os.listdir(folder_path) if img.endswith(".jpg")])

    command = [
        "ffmpeg",
        "-framerate", str(fps),
        "-i", os.path.join(folder_path, "%d.jpg"),
        "-i", audio_path,
        "-c:v", "hevc_nvenc",
        "-preset", "lossless",
        output
    ]

    subprocess.run(command)

def process_frame(args):
    i, video_path = args
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, i)
    ret, frame = cap.read()
    if ret:
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.imwrite(f'./frames/{i}.jpg', gray_frame)

#動画をフレームごとに切り出す
def gen_frames_img(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    assert cap.isOpened() != 0, 'not opened'
    if cap.isOpened():
        os.makedirs('frames', exist_ok=True)
        base_path = os.path.join('frames')
        digit = len(str(int(cap.get(cv2.CAP_PROP_FRAME_COUNT))))
        frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        for i in tqdm.tqdm(range(frames)):
            if not os.path.isfile('./frames/'+str(i)+'.jpg'):
                ret, frame = cap.read()
                if ret:
                    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    cv2.imwrite('./frames/'+str(i)+'.jpg', gray_frame)
    return fps, frames

#ランダムドットを生成
def gen_pattern(width, height):
    return np.random.randint(0, 256, (width, height))

#画像から深度マップを生成してステレオグラムを作成
def gen_stereogram(img_path, output, pattern_div):
    depth_map = Image.open(img_path).convert('L')
    depth_data = depth_map.load()

    out_img = Image.new("L", depth_map.size)
    out_data = out_img.load()
    pattern_width = depth_map.size[0] / pattern_div
    pattern = gen_pattern(int(pattern_width), depth_map.size[1])

    for x in range(depth_map.size[0]):
        for y in range(depth_map.size[1]):
            if x < pattern_width:
                out_data[x, y] = int(pattern[x, y])
            else:
                shift = depth_data[x, y] / pattern_div
                out_data[x, y] = out_data[int(x - pattern_width + shift), y]

    os.makedirs(os.path.dirname(output), exist_ok=True)
    out_img.save(output)