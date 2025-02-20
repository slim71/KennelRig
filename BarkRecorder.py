import sys
import cv2
import time
import pyaudio
import wave
import threading
import subprocess


class BarkRecorder:
    rate: int
    frames_per_buffer: int
    channels: int
    filename: str
    part_number: int
    format: int
    audio_frames: list
    running: bool
    listener: pyaudio.PyAudio
    audio_filename: str
    stream: pyaudio.Stream
    audio_thread: threading.Thread
    start_event: threading.Event
    start_time: float

    def __init__(self, start_event: threading.Event, rate: int, frames_per_buffer: int = 1024, channels: int = 1, audio_file: str = "audio"):
        # Rate of device: int(self.listener.get_default_input_device_info()["defaultSampleRate"])
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer
        self.channels = channels
        self.filename = audio_file
        self.part_number = 1
        self.format = pyaudio.paInt16
        self.audio_frames = []
        self.running = False
        self.audio_thread = None
        self.start_event = start_event
        self.start_time = None

        self.listener = pyaudio.PyAudio()
        print(f"device rate: {int(self.listener.get_default_input_device_info()['defaultSampleRate'])}")
        self.audio_filename = f"{self.filename}_{self.part_number}.wav"
        self.stream = self.listener.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.frames_per_buffer,
        )

    def record(self):
        # Wait until signaled to start
        self.start_event.wait()
        self.running = True
        self.start_time = time.time()
        self.stream.start_stream()
        self.first_buffer_time = None  # New: to capture timestamp of the first audio buffer

        while self.running and self.stream.is_active():
            try:
                data = self.stream.read(self.frames_per_buffer, exception_on_overflow=False)
                # On the first successful read, record the timestamp
                if self.first_buffer_time is None:
                    self.first_buffer_time = time.time()
                    print("Audio first buffer timestamp:", self.first_buffer_time)
            except Exception as e:
                print("Error reading from stream:", e)
                break
            self.audio_frames.append(data)
        print("Exiting audio recording thread.")

    def stop(self):
        # Signal the recording thread to stop
        self.running = False

        # Optionally, wait for the thread to finish if you need to
        if self.audio_thread is not None:
            self.audio_thread.join()

        if self.stream.is_active():
                self.stream.stop_stream()

        self.stream.close()

        # Get the sample width before terminating the listener
        sampwidth = self.listener.get_sample_size(self.format)
        self.listener.terminate()

        with wave.open(self.audio_filename, "wb") as waveFile:
            waveFile.setnchannels(self.channels)
            waveFile.setsampwidth(sampwidth)
            waveFile.setframerate(self.rate)
            waveFile.writeframes(b"".join(self.audio_frames))

    def start(self):
        self.audio_thread = threading.Thread(target=self.record)
        self.audio_thread.start()

