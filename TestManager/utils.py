import re
import socket
from typing import List
from config import Config

def letter_to_qb_url(letter):
    if letter == 'J':
        return Config.JAVA_QB
    elif letter== 'P':
        return Config.PYTHON_QB
    elif letter == 'C':
        return Config.C_QB

def qb_to_letter(url):
    if url == Config.JAVA_QB:
        return 'J'
    elif url== Config.PYTHON_QB:
        return 'P'
    elif url == Config.C_QB:
        return 'C'
    
def active_qbs() -> List[str]: 
    '''Tries to create a connection to each QB in config.py & returns the active QBs'''
    return [url for url in [Config.JAVA_QB, Config.PYTHON_QB, Config.C_QB] if ping_qb(url)]

def ping_qb(url):
    url = re.sub(r'^https?://', '', url) # remove http/https from start of url
    url, port = url.split(':')  # extract port number from URL
    try:
        socket.create_connection((url, int(port)))
        return True
    except ConnectionError:
        return False

def parse_attempts(attempt):
    response = {}
    if attempt <= 3:
        response['state'] = "active"
    elif attempt == 4:
        response['state'] = "wrong"
        attempt -= 3
    else:
        response['state'] = "correct"
        attempt -= 4
    response['attempt'] = attempt
    return response
