import time
import pyaudio
import wave
import threading


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

    def __init__(
        self,
        start_event: threading.Event,
        rate: int,
        frames_per_buffer: int = 1024,
        channels: int = 1,
        audio_file: str = "audio",
    ):
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
        self.first_buffer_time = None

        self.listener = pyaudio.PyAudio()
        print(
            f"device rate: {int(self.listener.get_default_input_device_info()['defaultSampleRate'])}"
        )
        self.audio_filename = f"{self.filename}_{self.part_number}.wav"
        self.stream = self.listener.open(
            format=self.format,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.frames_per_buffer,
            stream_callback=self.record
        )

    def start(self):
        self.running = True
        self.audio_thread = threading.Thread(target=self.standalone_thread)
        self.audio_thread.start()

    def standalone_thread(self):
        self.start_event.wait()
        self.start_time = time.time()
        self.stream.start_stream()

    def stop(self):
        self.running = False

        # Stop the stream gracefully.
        if self.stream.is_active():
            self.stream.stop_stream()
        self.stream.close()
    
        sampwidth = self.listener.get_sample_size(self.format)
        self.listener.terminate()

        with wave.open(self.audio_filename, "wb") as waveFile:
            waveFile.setnchannels(self.channels)
            waveFile.setsampwidth(sampwidth)
            waveFile.setframerate(self.rate)
            waveFile.writeframes(b"".join(self.audio_frames))

    def record(self, in_data, frame_count, time_info, status_flags):
        # Callback: called automatically whenever new audio data is available.
        # It runs in a separate thread.
        if self.first_buffer_time is None:
            self.first_buffer_time = time.time()
            print("Audio first buffer timestamp:", self.first_buffer_time)
        
        # Store the incoming data
        self.audio_frames.append(in_data)
        
        # Continue recording if running, else signal completion.
        return (None, pyaudio.paContinue) if self.running else (None, pyaudio.paComplete)
