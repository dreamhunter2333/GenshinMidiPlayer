import time
import mido
import click
import logging
import pyautogui

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


def allToCMajor(file_name, force):
    note_temp = set(
        msg.note
        for msg in mido.MidiFile(file_name)
        if msg.type == "note_on"
    )
    res = [
        i
        for i in range(-48, 48)
        if not any((int(cur)+i) not in KEY_MAP for cur in note_temp)
    ]
    if not res and force:
        max_common = max(
            [
                (i, sum((int(cur)+i) in KEY_MAP for cur in note_temp))
                for i in range(-48, 48)
            ],
            key=lambda t: t[1]
        )
        note_temp = [
            int(int(cur)+max_common[0]) for cur in note_temp
        ]
        _logger.info(
            f"max_common={max_common} note_temp={note_temp}"
        )
        res = [max_common[0]]
    return res


def get_tempo(mid):
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                return msg.tempo
    else:
        return mido.midifiles.midifiles.DEFAULT_TEMPO


def playMidi(file_name, m_bpm, m_key_add):
    midi = mido.MidiFile(file_name)
    bpm = m_bpm or mido.tempo2bpm(get_tempo(midi))
    real_time = float(120 / bpm)
    _logger.info(
        f"Playing file_name={file_name}, bpm={bpm}, m_key_add={m_key_add}"
    )
    # Read midi file
    for msg in midi:
        if msg.type == "note_on" and KEY_MAP.get(int(msg.note)+m_key_add):
            sleep_time = float(msg.time) * real_time
            pyautogui.sleep(sleep_time)
            pyautogui.keyDown(KEY_MAP.get(int(msg.note)+m_key_add))
            pyautogui.keyUp(KEY_MAP.get(int(msg.note)+m_key_add))
        elif msg.type == "note_on":
            _logger.info(
                f"Skip {msg.note} {m_key_add}"
            )
        elif msg.type == "note_off":
            sleep_time = float(msg.time) * real_time
            pyautogui.sleep(sleep_time)


@ click.command()
@ click.option('--file_name', '-f', 'file_name', required=True, type=str)
@ click.option('--bpm', '-b', 'bpm', default=0, required=True, type=int)
@ click.option('--force', '-force', 'force', default=False, required=True, type=bool)
@ click.option('--wait_seconds', '-w', 'wait_seconds', default=5, required=True, type=int)
def main(file_name: str, force: bool, bpm: int, wait_seconds: int) -> None:
    _logger.info(
        f"Start file_name={file_name}, bpm={bpm}, wait_seconds={wait_seconds}"
    )

    note_add = 0
    key_add = allToCMajor(file_name, force)
    if not key_add:
        _logger.error("The midi file is too complex to play!")
        return
    _logger.info(f"key add values: {key_add}")
    note_add = int(input("请输入 key add value: "))

    _logger.info("5s 后开始播放")
    time.sleep(5)
    playMidi(file_name, bpm, note_add)
    _logger.info("Done.")


main()
