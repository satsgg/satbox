from dotenv import dotenv_values
import logging
import sys
import os

config = {
    **dotenv_values(".env")
}

if config['PYTHON_ENV'] == "production":
    config.update(**dotenv_values(".env.production"))

required_env_vars = [
    'PYTHON_ENV',
    'RTMP_URL',
    'PLAYLIST_URL',
    'DUMMY_AUDIO',
    'FONT_FILE'
]
for env_var in required_env_vars:
    assert env_var in config

config['fontfile'] = f'{os.getcwd()}/{config["FONT_FILE"]}'
config['dummy_audio'] = f'{os.getcwd()}/{config["DUMMY_AUDIO"]}'
config['dummy_video'] = f'{os.getcwd()}/{config["DUMMY_VIDEO"]}'

satbox_logger = logging.getLogger("satbox_logger")
satbox_logger.setLevel(logging.INFO)
satbox_formatter = logging.Formatter('%(asctime)s %(message)s')
satbox_handler = logging.FileHandler('./logs/satbox.log')
satbox_handler.setFormatter(satbox_formatter)
satbox_logger.addHandler(satbox_handler)

if config['PYTHON_ENV'] == 'development':
    satbox_logger.addHandler(logging.StreamHandler(sys.stdout))

# TODO: Custom reader thread?
yt_logger = logging.getLogger("yt_logger")
yt_logger.setLevel(logging.INFO)
yt_formatter = logging.Formatter('%(asctime)s %(message)s')
yt_handler = logging.FileHandler('./logs/yt.log')
yt_handler.setFormatter(yt_formatter)
yt_logger.addHandler(yt_handler)

# TODO: Format ffmpeg output for better logs
enc_logger = logging.getLogger("enc_logger")
enc_logger.setLevel(logging.INFO)
enc_formatter = logging.Formatter('%(asctime)s %(message)s')
enc_handler = logging.FileHandler('./logs/encoder.log')
enc_handler.setFormatter(enc_formatter)
enc_logger.addHandler(enc_handler)

stream_logger = logging.getLogger("stream_logger")
stream_logger.setLevel(logging.INFO)
stream_formatter = logging.Formatter('%(asctime)s %(message)s')
stream_handler = logging.FileHandler('./logs/stream.log')
stream_handler.setFormatter(stream_formatter)
stream_logger.addHandler(stream_handler)