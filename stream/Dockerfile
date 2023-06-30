FROM python:3.9.10


WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY stream.py playlist.py config.py .env .env.production felinefriends.aac emptyscreen.jpg ./
COPY bebas_neue bebas_neue

CMD ["/usr/local/bin/python", "stream.py"]
