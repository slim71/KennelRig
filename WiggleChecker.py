"""WiggleChecker handles the video recording."""
import sys
import threading
import time

import cv2


class WiggleChecker:
    """Simple class to create a capturing video application."""

    camera: cv2.VideoCapture
    running: bool
    frame_width: int
    frame_height: int
    fps: float
    max_duration: int
    part_number: int
    filename: str
    fourcc: int
    writer: cv2.VideoWriter
    start_time: float
    stop_event: threading.Event

    def __init__(
        self,
        start_event: threading.Event,
        width: int = 640,
        height: int = 480,
        duration_min: int = 30,
        fps: float = 20.0,
        video_file: str = "video",
    ) -> None:
        """Construct a default object.

        Args:
            start_event (threading.Event): Event to wait upon before starting.
            width (int, optional): Width of the video to record. Defaults to 640.
            height (int, optional): Height of the video to record. Defaults to 480.
            duration_min (int, optional): Duration of portions to record in minutes. Defaults to 30.
            fps (float, optional): Frame4s per seconds of the recording. Defaults to 20.0.
            video_file (str, optional): Name of the resulting file. Defaults to "video".

        """
        self.running = False
        self.frame_width = width
        self.frame_height = height
        self.fps = fps
        self.max_duration = duration_min * 60  # 30 minutes in seconds
        self.part_number = 1
        self.filename = video_file
        self.start_event = start_event
        self.start_time = None
        self.stop_event = threading.Event()
        self.current_frame = None  # to share the latest frame with the main thread

        # 4-byte code used to specify the video codec
        self.fourcc = cv2.VideoWriter_fourcc(*"MJPG")  #  TODO: different if windows?

        # Video capturing channel
        self.camera = cv2.VideoCapture(0)  # Camera#0 aka first default camera
        if not self.camera.isOpened():
            print("Error: Could not open camera")
            sys.exit(1)

        # Writer to file
        self.writer = cv2.VideoWriter(
            filename=f"{self.filename}_{self.part_number}.avi",
            fourcc=self.fourcc,
            fps=self.fps,
            frameSize=(self.frame_width, self.frame_height),
            isColor=True,
        )

    def start(self) -> None:
        """Launch the video recording function using a thread."""
        self.running = True
        self.stop_event.clear()
        video_thread = threading.Thread(target=self.record)
        video_thread.daemon = True
        video_thread.start()

    def signal_stop(self) -> None:
        """Respond to the stop signal."""
        self.running = False
        self.stop_event.set()

    def stop(self) -> None:
        """Stop the object functionalities."""
        # When everything done, release the capture
        if self.camera.isOpened():
            self.camera.release()
        self.writer.release()

    def display(self) -> None:
        """Run the display loop on the main thread."""
        while self.running:
            if self.current_frame is not None:
                cv2.imshow("Video Capture", self.current_frame)

            # Check for 'q' key press
            if cv2.waitKey(10) == ord("q"):
                print("q pressed, stopping...")
                self.signal_stop()
                break

            time.sleep(0.01)  # Prevent a tight loop

        print("out of while loop")

    def record(self) -> None:
        """Record the video."""
        # Wait until signaled to start
        self.start_event.wait()
        self.start_time = time.time()
        self.first_frame_time = None

        while self.running and self.camera.isOpened():
            # Capture frame-by-frame
            ret, frame = self.camera.read()
            if not ret:
                print("Error: Could not read frame")
                break

            # On first frame, record the timestamp
            if self.first_frame_time is None:
                self.first_frame_time = time.time()
                print("Video first frame timestamp:", self.first_frame_time)

            # Operations on video here, if needed
            # TODO: night time

            # Write the frame to the video file
            self.writer.write(frame)
            self.current_frame = frame

        print("Video recording thread exiting, signaling stop")
        self.signal_stop()

    def get_video_feature(self, prop_id: int) -> any:
        """Getter function for a property.

        Args:
            prop_id (int): Property to gather.

        Returns:
            any: Current value of the property.

        """
        return self.camera.get(prop_id)  # prop_id in [0;18]

    def set_video_feature(self, prop_id: int, value: any) -> None:
        """Set a property value.

        Args:
            prop_id (int): Property to change.
            value (any): Value to set.

        """
        self.camera.set(prop_id, value)  # prop_id in [0;18]


# TODO: divide in parts
# # Check if 30 minutes have passed
# if time.time() - start_time >= max_duration:
#     out.release()
#     recording = False
#     audio_thread.join()
#     part_number += 1
#     out = cv2.VideoWriter(f'output_part_{part_number}.avi', fourcc, fps, (frame_width, frame_height))
#     audio_thread = threading.Thread(target=record_audio, args=(f'audio_part_{part_number}.wav',))
#     recording = True
#     audio_thread.start()
#     start_time = time.time()
