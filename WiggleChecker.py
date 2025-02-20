import sys
import cv2
import time
import threading


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

    def __init__(
        self,
        start_event: threading.Event,
        width: int = 640,
        height: int = 480,
        duration_min: int = 30,
        fps: float = 20.0,
        video_file: str = "video",
    ):
        """Construct a default object."""
        self.running = False
        self.frame_width = width
        self.frame_height = height
        self.fps = fps
        self.max_duration = duration_min * 60  # 30 minutes in seconds
        self.part_number = 1
        self.filename = video_file
        self.start_event = start_event
        self.start_time = None
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

    def record(self):
        # Wait until signaled to start
        self.start_event.wait()
        self.start_time = time.time()
        self.first_frame_time = (
            None  # New: to capture timestamp of the first audio buffer
        )

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

            # Display the resulting frame
            cv2.imshow("Video Capture", frame)

            # Press 'q' to exit the video capture TODO: how to also use the X?
            status = cv2.getWindowProperty("Video Capture", cv2.WND_PROP_VISIBLE)
            if cv2.waitKey(10) == ord("q"):
                break

        self.close()  # TODO: close from main thread

    def start(self):
        """Launch the video recording function using a thread."""
        self.running = True
        video_thread = threading.Thread(target=self.record)
        video_thread.start()

    def close(self):
        # When everything done, release the capture
        if self.running:
            self.running = False
            self.camera.release()
            self.writer.release()
            cv2.destroyAllWindows()

    def get_video_feature(self, propId):
        return self.camera.get(propId)  # propId in [0;18]

    def set_video_feature(self, propId, value):
        self.camera.set(propId, value)  # propId in [0;18]


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
