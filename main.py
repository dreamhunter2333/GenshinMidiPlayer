import time
from typing import Dict
import mido
import click
import logging
import pyautogui

from pydantic import BaseModel


class Settings(BaseModel):
    keymap: Dict[int, str]


KEY_MAP = {
    60: 'z', 62: 'x', 64: 'c', 65: 'v', 67: 'b', 69: 'n', 71: 'm',
    72: 'a', 74: 's', 76: 'd', 77: 'f', 79: 'g', 81: 'h', 83: 'j',
    84: 'q', 86: 'w', 88: 'e', 89: 'r', 91: 't', 93: 'y', 95: 'u',
    0: 'p'
}

pyautogui.PAUSE = 0
_logger = logging.Logger(__name__)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('[原神 MiDi 弹琴][%(levelname)s] %(message)s')
ch.setFormatter(formatter)
_logger.addHandler(ch)


def get_tempo(mid: mido.MidiFile) -> int:
    tempos = [
        msg.tempo
        for track in mid.tracks
        for msg in track
        if msg.type == 'set_tempo'
    ]
    if len(tempos) == 1:
        return tempos[0]
    elif len(tempos) > 1:
        int(input(f"请输入 key add value: {tempos}"))
    return mido.midifiles.midifiles.DEFAULT_TEMPO


def playMidi(file_name: str, m_bpm: int, m_key_add: int, keymap: Dict[int, str]) -> None:
    midi = mido.MidiFile(file_name)
    bpm = m_bpm or mido.tempo2bpm(get_tempo(midi))
    real_time = float(120 / bpm)
    _logger.info(
        f"Playing file_name={file_name}, bpm={bpm}, m_key_add={m_key_add}"
    )
    # Read midi file
    for msg in midi:
        if msg.type == "note_on" and keymap.get(int(msg.note)+m_key_add):
            sleep_time = float(msg.time) * real_time
            pyautogui.sleep(sleep_time)
            pyautogui.keyDown(keymap.get(int(msg.note)+m_key_add))
            pyautogui.keyUp(keymap.get(int(msg.note)+m_key_add))
        elif msg.type == "note_on":
            _logger.info(
                f"Skip {msg.note} {m_key_add}"
            )
        elif msg.type == "note_off":
            sleep_time = float(msg.time) * real_time
            pyautogui.sleep(sleep_time)


@click.command()
@click.option('--file_name', '-f', 'file_name', required=True, type=str)
@click.option('--bpm', '-b', 'bpm', default=0, required=True, type=int)
@click.option('--wait_seconds', '-w', 'wait_seconds', default=5, required=True, type=int)
@click.option('--keymap_file', '-k', 'keymap_file', default="keymap.json", type=str)
def main(file_name: str, bpm: int, wait_seconds: int, keymap_file: str) -> None:
    _logger.info(
        f"Start file_name={file_name}, bpm={bpm}, wait_seconds={wait_seconds}, keymap_file={keymap_file}"
    )

    keymap = Settings.parse_file(
        keymap_file
    ).keymap if keymap_file else KEY_MAP

    # 调整 key
    note_add = 0
    note_temp = set(
        msg.note
        for msg in mido.MidiFile(file_name)
        if msg.type == "note_on"
    )
    key_add = [
        i
        for i in range(-48, 48)
        if not any((int(cur)+i) not in keymap for cur in note_temp)
    ]
    if not key_add:
        _logger.error("The midi file is too complex to play!")
        return

    if note_add not in key_add:
        _logger.info(f"key add values: {key_add}")
        note_add = int(input("请输入 key add value: "))

    _logger.info(f"{wait_seconds} s 后开始播放")
    time.sleep(5)
    playMidi(file_name, bpm, note_add, keymap)
    _logger.info("Done.")


main()
