"""The KennelRig file is the core of the application."""
import signal
import subprocess
import threading

import cv2

from BarkRecorder import BarkRecorder
from WiggleChecker import WiggleChecker


class KennelRig:
    """Simple class to merge video and audio recordings."""

    camera: WiggleChecker
    mic: BarkRecorder
    video_filename: str
    audio_filename: str
    parts: int
    start_event: threading.Event

    def __init__(
        self, video_file: str = "video", audio_file: str = "audio", filename: str = "recording",
    ) -> None:
        """Construct an object.

        Args:
            video_file (str, optional): Video file name. Defaults to "video".
            audio_file (str, optional): Audio file name. Defaults to "audio".
            filename (str, optional): Name for the final merged video. Defaults to "recording".

        """
        self.video_filename = video_file
        self.audio_filename = audio_file
        self.filename = filename
        self.parts = 1
        self.start_event = threading.Event()
        self.camera = WiggleChecker(start_event=self.start_event)
        self.mic = BarkRecorder(start_event=self.start_event, rate=16000)
        self.shutdown_initiated = False

        # Register signal handler
        signal.signal(signal.SIGINT, self.signal_handler)

    def start(self) -> None:
        """Start the entire Rig."""
        self.camera.start()
        self.mic.start()
        self.start_event.set()  # Signal actual start

        self.camera.display()

        cv2.destroyAllWindows()
        self.mic.stop()
        self.camera.stop()
        self.merge()  # TODO: only if not ctrl+c?

    def signal_handler(self, sig, frame) -> None:  # noqa: ANN001, ARG002
        """Handle the SIGINT signal.

        Args:
            sig (int): The signal number received.
            frame (FrameType, optional): The current stack frame (or None) at the time of the signal.

        """
        if not self.shutdown_initiated:
            print("\nCtrl+C detected! Stopping...")
            self.shutdown_initiated = True

            # Force video and audio to stop.
            self.camera.signal_stop()
            self.mic.stop()

    def merge(self) -> None:
        """Merge audio and video parts in a single file."""
        # Calculate the relative delays if available.
        video_delay = (
            self.camera.first_frame_time - self.camera.start_time
            if self.camera.first_frame_time
            else 0.0
        )
        audio_delay = (
            self.mic.first_buffer_time - self.mic.start_time if self.mic.first_buffer_time else 0.0
        )

        # Compute the offset difference: positive if audio starts later than video.
        offset_diff = audio_delay - video_delay
        print("Calculated video delay:", video_delay)
        print("Calculated audio delay:", audio_delay)
        print("Calculated offset (audio - video):", offset_diff)

        # Merge audio and video files
        for i in range(1, self.parts + 1):
            video_file = f"{self.video_filename}_{i}.avi"
            audio_file = f"{self.audio_filename}_{i}.wav"
            output_file = f"{self.filename}_{i}.avi"
            # If audio is delayed, apply an offset.
            if offset_diff > 0:
                command = [
                    "ffmpeg",
                    "-i",
                    video_file,
                    "-itsoffset",
                    str(offset_diff),
                    "-i",
                    audio_file,
                    "-c:a",
                    "aac",
                    "-async",
                    "1",
                    "-ss",
                    "-1",  # CHECK: might not always be enough delay
                    "-y",  # Overwrite without prompting
                    output_file,
                ]
            else:
                command = [
                    "ffmpeg",
                    "-i",
                    video_file,
                    "-i",
                    audio_file,
                    "-c:a",
                    "aac",
                    "-async",
                    "10",
                    "-y",
                    output_file,
                ]
            print("Running ffmpeg command:", " ".join(command))
            subprocess.call(command)


if __name__ == "__main__":
    KennelRig().start()
