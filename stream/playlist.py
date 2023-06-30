from config import config
import logging
import requests

satbox_logger = logging.getLogger("satbox_logger")

class Playlist:
    def __init__(self):
        self.a = True
        self.l_current = 0

    def next(self, pop=True):
        query = f'{config["PLAYLIST_URL"]}/next{("?pop=true" if pop else "")}'
        try: 
            r = requests.get(query).json()
            if not r:
                satbox_logger.debug('Remote queue is empty!')
                return None
            return r
        except requests.ConnectionError as e:
            satbox_logger.warn(f'remote playlist unreachable:\n{e}')
        except Exception as e:
            satbox_logger.warn(f'error retrieving next video:\n{e}')

        return None
        # return False