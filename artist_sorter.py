#!/usr/bin/python3

import os
import sys
from os.path import isfile, join
from pathlib import Path
import subprocess
import logging

log_dir = "../logs/artist_sorter.log"
logger = logging.getLogger(__name__)
logging.basicConfig(filename=log_dir, encoding='utf-8', level=logging.DEBUG, format='%(asctime)s: %(levelname)s %(message)s')


artist_dict = {}
track_dict = {}

source_dir = "../crypt"
# This is where the directory structure will be created:
target_dir = "../Music/crypt/test"

def add_meta_to_dict(track, meta_data):
    meta_list = (meta_data).split("\n")
    artist = ""
    album = ""
    title = ""
    unknown_counter = 0
    for ix, i in enumerate(meta_list):
        if ("artist=" in i):
            artist = (meta_list[ix][len("artist="):]).replace(" ",  "_").replace("'", "").replace("/", "-")
        if ("title=" in i):
            title = (meta_list[ix][len("title="):]).replace(" ", "_").replace("'",  "").replace("/", "-")
            if (len(title)==0):
                title = f"unknown_title_{unknown_counter}"
                unknown_counter += 1
        if ("album=" in i):
            album = (meta_list[ix][len("album="):]).replace(" ", "_").replace("'",  "").replace("/", "-")
            if (len(album)==0):
                album = f"unknown_album_{unknown_counter}"
                unknown_counter += 1

    if artist not in artist_dict:
        artist_dict[artist] = {}
    if album not in artist_dict[artist]:
        artist_dict[artist][album] = []
    artist_dict[artist][album].append(title)
    track_dict[track] = [artist, album, title]


def get_meta_data(file_name):
    return_val = None
    cmd_1 = f"ffprobe -v quiet {file_name} -show_entries format_tags "
    cmd_2 = "| awk 'BEGIN{FS=\":\"};{print $2}' | grep 'artist\|title\|album'"
    cmd = cmd_1 + " " + cmd_2
    try:
        # Use shell=True to run the command in a shell
        result = subprocess.run(cmd, shell=True, capture_output=True, check=True, text=True)
        return_val = result.stdout
        logger.info(f"get_meta_data:: {return_val}.")
    except subprocess.CalledProcessError as e:
        print(f"Subprocess error on file {file_name}; see logs at {log_dir}.")
        logger.warning(f"Subprocess error on file {file_name}.")
        logger.warning(f"    Error: {e}")
        logger.warning(f"    Standard Output: {e.stdout}")
        logger.warning(f"    Standard Error: {e.stderr}")
    return return_val


def get_file_names():
    file_names = []
    dirs = os.listdir(source_dir)
    for directory in dirs:
        d = join(source_dir, directory)
        _f = [os.path.join(d, f) for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))]
        for mf in _f:
            if (mf[-3:]=="m4a"):
                file_names.append(mf)
                logger.info(f"get_file_names:: found file <{mf}>.")
    #print(file_names[9], len(file_names))
    return file_names


def create_directories(target_path, dic):
    #print(f"creating dirs:: album dict: {dic}.")
    for artist in dic:
        for album in dic[artist]:
            logger.info(f"create_directores:: creating directory <{album}> in <{artist}>.")
            Path(os.path.join(target_path, artist, album)).mkdir(parents=True, exist_ok=True)
    return

def move_track(track, target_path):
    cp_or_mv = ["cp", "mv"]
    return_val = None
    artist = track_dict[track][0]
    album = track_dict[track][1]
    title = track_dict[track][2]
    #print(f"move_track:: '{artist}', '{album}', '{title}'")
    ext = ".m4a"
    new_name = title.replace(" ", "_") + ext
    _target_path = os.path.join(target_path, artist, album, new_name)
    cmd = f"{cp_or_mv[0]} {track} " + "'" + _target_path + "'"
    logger.info(f"move_trace:: command <{cmd}>.")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, check=True, text=True)
        return_val = result.stdout
        logger.info(f"move_track:: subprocess stdout: {return_val}")
    except subprocess.CalledProcessError as e:
        print(f"Subprocess error on cmd: '{cmd}'; see logs at {log_dir}.")
        logger.warning(f"Subprocess error on cmd '{cmd}'.")
        logger.warning(f"    Error: {e}")
        logger.warning(f"    Standard Output: {e.stdout}")
        logger.warning(f"    Standard Error: {e.stderr}")
    return return_val


if __name__ == "__main__":
    file_names = get_file_names()
    for track in file_names:
        meta_data = get_meta_data(track)
        if (meta_data != None):
            add_meta_to_dict(track, meta_data)
        else:
            print(f"Metadata error on {track}")
    create_directories(target_dir, artist_dict)
    for track in track_dict:
        move_track(track, target_dir)
    print("Done.")
