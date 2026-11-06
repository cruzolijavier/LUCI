"""Microphone recording for dictating to the assistant.

Records with QtMultimedia (no extra libraries), saves a 16-bit mono WAV in the
LUCI folder and it is transcribed by OpenAI. The text goes to the input box;
it is not sent on its own.
"""

from __future__ import annotations

from array import array
import math
import sys
import time
import wave

from PySide6.QtCore import QObject, QTimer, Signal

from . import config as cfg

try:
    from PySide6.QtMultimedia import QAudioFormat, QAudioSource, QMediaDevices
    HAVE_AUDIO = True
except ImportError:  # pragma: no cover - PySide6 without the multimedia add-on
    HAVE_AUDIO = False


class AudioRecorder(QObject):
    seconds = Signal(int)
    finished = Signal(str)     # path of the WAV
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._source = None
        self._io = None
        self._data = bytearray()
        self._format = None
        self._start_time = 0.0
        self._clock = QTimer(self)
        self._clock.setInterval(250)
        self._clock.timeout.connect(self._tick)

    @property
    def recording(self) -> bool:
        return self._source is not None

    def start(self):
        if self.recording:
            return
        if not HAVE_AUDIO:
            self.error.emit("This PySide6 has no QtMultimedia, so the microphone cannot be used.")
            return
        device = QMediaDevices.defaultAudioInput()
        if device.isNull():
            self.error.emit("No microphone was found on this computer.")
            return
        fmt = QAudioFormat()
        fmt.setSampleRate(16000)
        fmt.setChannelCount(1)
        fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)
        if not device.isFormatSupported(fmt):
            fmt = device.preferredFormat()
        self._format = fmt
        self._data = bytearray()
        self._source = QAudioSource(device, fmt, self)
        self._io = self._source.start()
        if self._io is None:
            self._source = None
            self.error.emit("The microphone could not be opened (is another application using it?).")
            return
        self._io.readyRead.connect(self._read)
        self._start_time = time.monotonic()
        self._clock.start()

    def _read(self):
        if self._io is not None:
            chunk = bytes(self._io.readAll())
            if chunk:
                self._data += chunk

    def _tick(self):
        elapsed = int(time.monotonic() - self._start_time)
        self.seconds.emit(elapsed)
        if elapsed >= cfg.MAX_AUDIO_SECONDS:
            self.stop()

    def _to_mono16(self, data: bytes) -> array:
        """Bytes in the microphone's format -> 16-bit mono samples."""
        fmt = self._format
        kind = fmt.sampleFormat()
        if kind == QAudioFormat.SampleFormat.Int16:
            values = array("h", data[:len(data) // 2 * 2])
            scale = 1.0
        elif kind == QAudioFormat.SampleFormat.Int32:
            values = array("i", data[:len(data) // 4 * 4])
            scale = 1 / 65536
        elif kind == QAudioFormat.SampleFormat.Float:
            values = array("f", data[:len(data) // 4 * 4])
            scale = 32767.0
        else:  # UInt8
            values = array("h", [(b - 128) * 256 for b in data])
            scale = 1.0
        if sys.byteorder != "little" and kind != QAudioFormat.SampleFormat.UInt8:
            values.byteswap()
        channels = max(1, fmt.channelCount())
        mono = array("h")
        for start in range(0, len(values) - channels + 1, channels):
            sample = sum(values[start:start + channels]) / channels * scale
            mono.append(int(max(-32768, min(32767, sample))))
        return mono

    @staticmethod
    def has_voice(samples: array, rate: int) -> bool:
        """Voice if at least 0.24 s of 30 ms windows pass a minimum energy (room noise gives
        single peaks, and with empty audio transcription models invent text)."""
        window = max(1, int(rate * 0.03))
        loud = 0
        for start in range(0, len(samples) - window + 1, window):
            block = samples[start:start + window]
            if math.sqrt(sum(x * x for x in block) / window) > 250:
                loud += 1
                if loud >= 8:
                    return True
        return False

    def cancel(self):
        self._halt()
        self._data = bytearray()

    def _halt(self):
        self._clock.stop()
        if self._source is not None:
            try:
                if self._io is not None:
                    self._read()
                self._source.stop()
            except RuntimeError:
                pass
            self._source.deleteLater()
        self._source = None
        self._io = None

    def stop(self):
        if not self.recording:
            return
        self._halt()
        samples = self._to_mono16(bytes(self._data))
        self._data = bytearray()
        rate = self._format.sampleRate()
        if len(samples) < rate * 0.4:
            self.error.emit("The recording is too short.")
            return
        if not self.has_voice(samples, rate):
            self.error.emit("No sound was captured. Check the microphone and that Windows lets desktop apps "
                            "use it (Settings > Privacy > Microphone).")
            return
        path = cfg.cache_dir() / "dictation.wav"
        if sys.byteorder != "little":
            samples.byteswap()
        with wave.open(str(path), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(rate)
            handle.writeframes(samples.tobytes())
        self.finished.emit(str(path))
