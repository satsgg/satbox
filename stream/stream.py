from subprocess import Popen, PIPE, DEVNULL
import os
import signal
import threading
import logging
import time
from playlist import Playlist
from config import config

COPY_BUFSIZE = 65424

os.makedirs('./logs', exist_ok=True)

satbox_logger = logging.getLogger("satbox_logger")
yt_logger = logging.getLogger("yt_logger")
enc_logger = logging.getLogger("enc_logger")
stream_logger = logging.getLogger("stream_logger")

# Writer thread (read from yt-dlp and write to FFmpeg in chunks of COPY_BUFSIZE bytes).
def writer(yt_dlp_proc, encoder_proc):
    while True:
        yt_dlp_buf = yt_dlp_proc.stdout.read(COPY_BUFSIZE)
        if not yt_dlp_buf:
            break

        # NOTE: when video is cut off at 5 minutes, we get BrokenPipeError here.
        # actually getting a mixture of Value and broken pipe error....
        try:
            encoder_proc.stdin.write(yt_dlp_buf)
        except BrokenPipeError:
            enc_logger.warning("Broken Pipe Error: Decoder pipe most likely closed due hitting duration max limit")
            break
        except ValueError:
            enc_logger.warning("Value Error: Decoder pipe most likely closed due hitting duration max limit")
            break
    
    encoder_proc.stdin.close()  # Close stdin pipe (closing stdin "pushes" the remaining data to stdout).
    encoder_proc.wait()  # Wait for sub-process finish execution.


def ffmpeg_stderr_reader(s, t):
    if t == 'encoder':
        logger = enc_logger
    elif t == 'stream':
        logger = stream_logger
    else:
        logger = yt_logger
    
    try:
        for line in s:
            logger.info(line)
    except ValueError:
        pass

def dummy_stopper(playlist, dummy_proc_pid):
    while True:
        video = playlist.next(pop=False)
        if not video:
            time.sleep(5)
            continue
        os.kill(dummy_proc_pid, signal.SIGKILL) 
        break

def checkContinue(playlist, proc_pid):
    nowPlaying = playlist.next(pop=False)
    if not nowPlaying['video'] or nowPlaying['continueAmount'] < nowPlaying['continueTarget']:
        satbox_logger.info('stopping the current video!')
        os.kill(proc_pid, signal.SIGKILL)
        return False
    else:
        satbox_logger.info('continuing the current video!')
        # TODO: Maybe refactor the logic?
        # next -> next, next(pop) -> tick?
        # pop to bump the playtime and keep playing the current video
        playlist.next(pop=True)
        return True

class ContinueTimer():
    def __init__(self, interval, f, *args, **kwargs):
        self.interval = interval
        self.f = f
        self.args = args
        self.kwargs = kwargs
        self.timer = None

    def start(self):
        self.timer = threading.Timer(self.interval, self.callback)
        self.timer.start()
    
    def callback(self):
        shouldContinue = self.f(*self.args, **self.kwargs)
        if shouldContinue:
            self.cancel()
            self.start()
    
    def cancel(self):
        self.timer.cancel()

if __name__ == "__main__":
    if config['PYTHON_ENV'] == 'development':
        satbox_logger.info('Starting ffplay')
        ffplay_cmd = ['ffplay', "-hide_banner", "-nostats",'-listen', '1', '-i', config['RTMP_URL']] # Start the TCP server first, before the sending client.    
        satbox_logger.info(f'ffplay command:\n"{" ".join(ffplay_cmd)}"')
        # TODO: Could help to have ffplay logs...
        # ffplay_process = Popen(ffplay_cmd, stderr=DEVNULL)  # Use FFplay sub-process for receiving the RTMP video.
        ffplay_process = Popen(ffplay_cmd)  # Use FFplay sub-process for receiving the RTMP video.


    stream_cmd = [
        "ffmpeg", 
        "-loglevel",
        "level+error" if config['PYTHON_ENV'] == 'production' else 'level+info',
        "-hide_banner", "-nostats",
        "-re",
        "-i", "-",
        "-preset", "veryfast",
        "-c:v", "libx264", # need this if already passing in as libx264? Maybe for yt-dlp output
        "-f", "flv",
        "-s", "1920x1080",
        "-b:v", "3000k", "-minrate", "3000k",
        "-maxrate", "3000k", "-bufsize", "3000k",
        "-r", "25", "-pix_fmt", "yuv420p",
        config['RTMP_URL']
    ]
    satbox_logger.info(f'Stream command:\n"{" ".join(stream_cmd)}"')

    stream_logger.info('Starting stream')
    stream_p = Popen(stream_cmd, stdin=PIPE, stderr=PIPE)
    stream_err_thread = threading.Thread(target=ffmpeg_stderr_reader, args=(stream_p.stderr, 'stream'))
    stream_err_thread.daemon = True
    stream_err_thread.start()

    playlist = Playlist()
    try: 
        while True:
            # nowPlaying = playlist.next()
            # video = nowPlaying['video']
            video = playlist.next()
            if not video:
                encoder_cmd = [
                   "ffmpeg",
                    "-loglevel",
                    "level+error" if config['PYTHON_ENV'] == 'production' else 'level+info',
                    "-hide_banner",
                    "-fflags", "+genpts",

                    # Empty screen
                    "-stream_loop", "-1",
                    "-f", "image2",
                    "-i", config["dummy_video"],

                    # Audio
                    "-stream_loop", "-1",
                    "-f", "aac",
                    "-i", config['dummy_audio'],

                    "-c:a", "copy",
                    "-c:v", "libx264",
                    "-r", "25",
                    "-s", "1920x1080",
                    "-f", "mpegts",
                    "-"
                ]

                satbox_logger.info(f'Encoder command:\n"{" ".join(encoder_cmd)}"')
                satbox_logger.info("Playing dummy video")

                with Popen(encoder_cmd, stdout=PIPE, stderr=PIPE) as encoder_p:
                    encoder_err_thread = threading.Thread(target=ffmpeg_stderr_reader, args=(encoder_p.stderr, 'encoder'))
                    encoder_err_thread.daemon = True
                    encoder_err_thread.start()

                    dummy_stopper_thread = threading.Thread(target=dummy_stopper, args=(playlist, encoder_p.pid))
                    dummy_stopper_thread.daemon = True
                    dummy_stopper_thread.start() 

                    while True:
                        encoder_buf = encoder_p.stdout.read(COPY_BUFSIZE)

                        if not encoder_buf:
                            break

                        stream_p.stdin.write(encoder_buf)

                dummy_stopper_thread.join()
                    
            else:
                # TODO: Construct URL
                # append duration to query
                url = "https://youtube.com/watch?v=" + video["videoId"]

                yt_dlp_cmd = [
                    "yt-dlp",
                    # "-q",
                    "-v",
                    # "-f", "webm",
                    # "-f", "'webm[height=720]'",
                    # TODO: Issue using ffmpeg as downloader is we lose audio
                    # need to debug the streams... But is ffmpeg as downloader worse?
                    # If use ffmpeg as downloader, might be able to remove encoder pipe?
                    # Might be easiest for now to use handle the broken pipe error that yt_dlp proc
                    # is experiencing, because the seeking and duration limit in encoder works
                    # "--downloader", "ffmpeg",
                    # TODO: Seeking here works except for the audio is gone...
                    # "--external-downloader-args","ffmpeg_i:-ss 10",
                    # TODO: Limiting duration works here... 
                    # "--external-downloader-args","ffmpeg_o:-t 10",
                    url,
                    "-o", "-"
                ]

                # TODO: Add light background to see text on white background
                # TODO: Draw text on output stream? To stop fontsize from scaling with video quality
                title = "\"[0:v]drawtext=" \
                    "fontfile=" + config['fontfile'] + "" \
                    ":fontsize=25:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=2:x=5:y=5:" \
                    "text='" + video["title"] +  "', " \
                    "drawtext=" \
                    "fontfile=" + config['fontfile'] + "" \
                    ":fontsize=20:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=2:x=5:y=30:" \
                    "text='" + video["author"] +  "'\""

                # NOTE: Removed encoding and just doing a copy. No more text overlay, but 
                # uses less CPU resources.
                # encoder_cmd = [
                #     "ffmpeg",
                #     # "-loglevel", "error",
                #     "-hide_banner", "-nostats",
                #     "-probesize", "32",
                #     # "-ss", "10",
                #     # TODO: Limiting duration here works.. breaks yt-dlp pipe though (only when video cut short at 5 minutes?)
                #     "-t", "300",
                #     "-i", "-",
                #     # "-c", "copy",
                #     "-lavfi",
                #     ] + shlex.split(title) + [
                #     # ] + shlex.split(author) + [
                #     "-map", "0:a",
                #     "-c:a", "copy",
                #     "-c:v", "libx264",
                #     # "-s", "1920x1080", # doesn't fix fontsize scaling on low res videos.
                #     "-f", "mpegts", 
                #     "-"
                # ]

                encoder_cmd = [
                    "ffmpeg",
                    "-loglevel",
                    "level+error" if config['PYTHON_ENV'] == 'production' else 'level+info',
                    "-hide_banner", "-nostats",
                    "-probesize", "32",
                    # "-t", "300",
                    "-i", "-",
                    "-c", "copy",
                    "-f", "mpegts", 
                    "-"
                ]

                satbox_logger.info(f'Encoder command:\n"{" ".join(encoder_cmd)}"')

                satbox_logger.info("Now playing: " + url)


                with Popen(yt_dlp_cmd, stdout=PIPE, stderr=PIPE) as yt_dlp_p:
                    yt_err_thread = threading.Thread(target=ffmpeg_stderr_reader, args=(yt_dlp_p.stderr, 'yt'))
                    yt_err_thread.daemon = True
                    yt_err_thread.start()

                    with Popen(encoder_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE) as encoder_p:
                        encoder_err_thread = threading.Thread(target=ffmpeg_stderr_reader, args=(encoder_p.stderr, 'encoder'))
                        encoder_err_thread.daemon = True
                        encoder_err_thread.start()

                        encoder_thread = threading.Thread(target=writer, args=(yt_dlp_p, encoder_p))
                        encoder_thread.start()  # Start writer thread.

                        t = ContinueTimer(300, checkContinue, playlist, encoder_p.pid)
                        t.start()

                        while True:
                            encoder_buf = encoder_p.stdout.read(COPY_BUFSIZE)

                            if not encoder_buf:
                                break

                            stream_p.stdin.write(encoder_buf)

                encoder_thread.join()  # Wait for writer thread to end.
                yt_dlp_p.wait()
                t.cancel() # cancel existing timer when video ends short

    except SystemExit:
        # this doesn't always trigger on sigint
        satbox_logger.info("Got close command")

    except KeyboardInterrupt:
        satbox_logger.info("keyboard interrupt!")

    finally:
        # encoder_p.stdin.close()
        encoder_p.wait()
        stream_p.stdin.close()  # Close stdin pipe (closing stdin "pushes" the remaining data to stdout).
        stream_p.wait()  # Wait for sub-process finish execution.
        if config['PYTHON_ENV'] == "development":
            ffplay_process.kill()  # Forcefully close FFplay sub-procesS
            satbox_logger.info('Closing ffplay')
