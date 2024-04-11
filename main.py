import s_modules as m
import os
import tqdm
from multiprocessing import Pool
import shutil

def path_check(path):
    paths = os.environ.get('PATH', '').split(os.pathsep)
    return any(path in s for s in paths)

def generate_stereogram(i):
    m.gen_stereogram('frames/'+str(i)+'.jpg','stereogram/'+str(i)+'.jpg', 6)

if __name__ == '__main__':
    print('checking is ffmpeg available')
    if path_check('ffmpeg.exe') or path_check('ffmpeg'):
        print('ffmpeg is available')
    else:
        print('ffmpeg is not available')
        print('please download ffmpeg')
        print('https://ffmpeg.org/download.html')
        os._exit(1)
    videofile = input('video path:')
    threads = 16
    print("generating images for each frame")
    os.makedirs('frames', exist_ok=True)
    shutil.rmtree('frames')
    video_info = m.gen_frames_img(videofile)
    fps = video_info[0]
    frames = video_info[1]

    if os.path.isfile('bgm.mp3'):
        os.remove('bgm.mp3')

    print("extracting audio")
    m.extract_audio(videofile, 'bgm.mp3')

    print("generating stereogram")
    #マルチスレッドで高速化(笑)
    os.makedirs('stereogram', exist_ok=True)
    shutil.rmtree('stereogram')
    with Pool(threads) as pool:
        list(tqdm.tqdm(pool.imap(generate_stereogram, range(frames)), total=frames))

    print("merging images")
    if os.path.isfile('out.mp4'):
        os.remove('out.mp4')
    m.merge_imgs('stereogram', 'bgm.mp3', 'out.mp4', fps)
