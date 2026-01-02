"""
Hexapod Zero Controller (High-Level)

Runs on Pi Zero 2W. Handles:
- UART communication with Pico
- Camera capture and OpenCV processing
- Web UI for remote control
- High-level path planning

Requires:
    pip install flask opencv-python-headless picamera2
"""

import serial
import threading
import time
import json
from queue import Queue, Empty

# Serial connection to Pico
PICO_SERIAL = '/dev/serial0'
BAUD_RATE = 115200


class PicoInterface:
    """UART interface to Pi Pico."""

    def __init__(self, port=PICO_SERIAL, baudrate=BAUD_RATE):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.response_queue = Queue()
        self.running = False
        self.reader_thread = None

        # Status cache
        self.last_imu = (0, 0, 0)
        self.last_dist = (-1, -1, -1)
        self.last_bat = (0, 0, 0)

    def connect(self):
        """Connect to Pico via serial."""
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=0.1)
            time.sleep(0.5)  # Wait for Pico to reset

            # Start reader thread
            self.running = True
            self.reader_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.reader_thread.start()

            # Wait for READY message
            response = self.wait_response(timeout=5)
            if response == 'READY':
                print("Pico connected and ready")
                return True
            else:
                print(f"Unexpected response: {response}")
                return False

        except Exception as e:
            print(f"Failed to connect to Pico: {e}")
            return False

    def disconnect(self):
        """Disconnect from Pico."""
        self.running = False
        if self.serial:
            self.serial.close()
            self.serial = None

    def _read_loop(self):
        """Background thread to read serial responses."""
        while self.running and self.serial:
            try:
                if self.serial.in_waiting:
                    line = self.serial.readline().decode().strip()
                    if line:
                        self._handle_response(line)
            except Exception as e:
                print(f"Serial read error: {e}")
            time.sleep(0.01)

    def _handle_response(self, response):
        """Handle response from Pico."""
        # Parse status updates
        if response.startswith('IMU:'):
            parts = response[4:].split(',')
            self.last_imu = tuple(float(p) for p in parts)
        elif response.startswith('DIST:'):
            parts = response[5:].split(',')
            self.last_dist = tuple(int(p) for p in parts)
        elif response.startswith('BAT:'):
            parts = response[4:].split(',')
            self.last_bat = (float(parts[0]), float(parts[1]), float(parts[2]))
        elif response.startswith('WARN:'):
            print(f"Warning from Pico: {response[5:]}")
        elif response.startswith('ERR:'):
            print(f"Error from Pico: {response[4:]}")

        # Queue all responses
        self.response_queue.put(response)

    def send_command(self, cmd):
        """Send command to Pico."""
        if not self.serial:
            return False
        try:
            self.serial.write(f"{cmd}\n".encode())
            return True
        except Exception as e:
            print(f"Send error: {e}")
            return False

    def wait_response(self, timeout=1.0):
        """Wait for response from Pico."""
        try:
            return self.response_queue.get(timeout=timeout)
        except Empty:
            return None

    def send_and_wait(self, cmd, timeout=2.0):
        """Send command and wait for response."""
        # Clear queue
        while not self.response_queue.empty():
            self.response_queue.get_nowait()

        if not self.send_command(cmd):
            return None

        return self.wait_response(timeout)

    # High-level commands
    def walk(self, dx, dy):
        """Walk in direction."""
        return self.send_and_wait(f"W:{dx},{dy}")

    def turn(self, angle):
        """Turn in place."""
        return self.send_and_wait(f"T:{angle}")

    def stop(self):
        """Stop and stand."""
        return self.send_and_wait("S")

    def set_gait(self, gait):
        """Set gait type (tripod, wave, ripple)."""
        return self.send_and_wait(f"G:{gait}")

    def set_height(self, height):
        """Set standing height in mm."""
        return self.send_and_wait(f"H:{height}")

    def center(self):
        """Center all servos."""
        return self.send_and_wait("C")

    def boot(self):
        """Run boot sequence."""
        return self.send_and_wait("B", timeout=5)

    def shutdown(self):
        """Run shutdown sequence."""
        return self.send_and_wait("D", timeout=5)

    def get_status(self):
        """Get Pico status."""
        return self.send_and_wait("?")

    def update_sensors(self):
        """Request sensor updates."""
        self.send_command("IMU")
        self.send_command("DIST")
        self.send_command("BAT")


class CameraProcessor:
    """Camera capture and processing using OpenCV."""

    def __init__(self, resolution=(640, 480), framerate=10):
        self.resolution = resolution
        self.framerate = framerate
        self.camera = None
        self.running = False
        self.frame = None
        self.frame_lock = threading.Lock()

    def start(self):
        """Start camera capture."""
        try:
            from picamera2 import Picamera2
            self.camera = Picamera2()
            config = self.camera.create_preview_configuration(
                main={"size": self.resolution}
            )
            self.camera.configure(config)
            self.camera.start()
            self.running = True
            print("Camera started")
            return True
        except Exception as e:
            print(f"Camera init failed: {e}")
            return False

    def stop(self):
        """Stop camera capture."""
        self.running = False
        if self.camera:
            self.camera.stop()
            self.camera.close()
            self.camera = None

    def capture_frame(self):
        """Capture a frame."""
        if not self.camera:
            return None
        try:
            frame = self.camera.capture_array()
            with self.frame_lock:
                self.frame = frame
            return frame
        except Exception as e:
            print(f"Capture error: {e}")
            return None

    def get_frame(self):
        """Get most recent frame."""
        with self.frame_lock:
            return self.frame

    def detect_obstacles(self, frame=None):
        """
        Simple obstacle detection using color/edge detection.

        Returns:
            list of (x, y, w, h) bounding boxes
        """
        if frame is None:
            frame = self.get_frame()
        if frame is None:
            return []

        try:
            import cv2
            import numpy as np

            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Apply Gaussian blur
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Edge detection
            edges = cv2.Canny(blurred, 50, 150)

            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL,
                                           cv2.CHAIN_APPROX_SIMPLE)

            # Filter and return bounding boxes
            obstacles = []
            min_area = 500  # Minimum contour area
            for contour in contours:
                if cv2.contourArea(contour) > min_area:
                    x, y, w, h = cv2.boundingRect(contour)
                    obstacles.append((x, y, w, h))

            return obstacles

        except Exception as e:
            print(f"Detection error: {e}")
            return []


class WebController:
    """Flask web server for remote control."""

    def __init__(self, pico, camera=None, port=5000):
        self.pico = pico
        self.camera = camera
        self.port = port
        self.app = None

    def create_app(self):
        """Create Flask application."""
        from flask import Flask, render_template_string, jsonify, request, Response

        app = Flask(__name__)

        HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Hexapod Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial; text-align: center; background: #1a1a1a; color: #fff; }
        .controls { display: grid; grid-template-columns: repeat(3, 80px); gap: 10px; justify-content: center; margin: 20px; }
        button { padding: 20px; font-size: 18px; border-radius: 10px; border: none; background: #4CAF50; color: white; cursor: pointer; }
        button:hover { background: #45a049; }
        button:active { background: #3d8b40; }
        .stop { background: #f44336; grid-column: 2; }
        .stop:hover { background: #da190b; }
        .status { background: #333; padding: 20px; margin: 20px; border-radius: 10px; }
        .gait-select { margin: 20px; }
        select, input { padding: 10px; font-size: 16px; }
        #video { max-width: 100%; border-radius: 10px; }
    </style>
</head>
<body>
    <h1>Hexapod Control</h1>

    <div class="controls">
        <button onclick="cmd('tl')">&#8630;</button>
        <button onclick="cmd('fwd')">&#8593;</button>
        <button onclick="cmd('tr')">&#8631;</button>
        <button onclick="cmd('left')">&#8592;</button>
        <button class="stop" onclick="cmd('stop')">STOP</button>
        <button onclick="cmd('right')">&#8594;</button>
        <button onclick="cmd('boot')">Boot</button>
        <button onclick="cmd('back')">&#8595;</button>
        <button onclick="cmd('shutdown')">Down</button>
    </div>

    <div class="gait-select">
        <select id="gait" onchange="setGait()">
            <option value="tripod">Tripod (Fast)</option>
            <option value="wave">Wave (Stable)</option>
            <option value="ripple">Ripple (Smooth)</option>
        </select>
        <input type="range" id="height" min="20" max="80" value="50" onchange="setHeight()">
        <span id="heightVal">50mm</span>
    </div>

    <div class="status">
        <div>IMU: <span id="imu">--</span></div>
        <div>Distance: <span id="dist">--</span></div>
        <div>Battery: <span id="bat">--</span></div>
    </div>

    <img id="video" src="/video_feed" alt="Camera">

    <script>
        function cmd(c) {
            fetch('/cmd/' + c).then(r => r.json()).then(d => console.log(d));
        }
        function setGait() {
            fetch('/gait/' + document.getElementById('gait').value);
        }
        function setHeight() {
            var h = document.getElementById('height').value;
            document.getElementById('heightVal').textContent = h + 'mm';
            fetch('/height/' + h);
        }
        function updateStatus() {
            fetch('/status').then(r => r.json()).then(d => {
                document.getElementById('imu').textContent =
                    'Roll: ' + d.imu[0].toFixed(1) + ' Pitch: ' + d.imu[1].toFixed(1);
                document.getElementById('dist').textContent =
                    'F: ' + d.dist[0] + ' L: ' + d.dist[1] + ' R: ' + d.dist[2] + ' mm';
                document.getElementById('bat').textContent =
                    d.bat[0].toFixed(1) + 'V ' + d.bat[2].toFixed(0) + '%';
            });
        }
        setInterval(updateStatus, 500);
    </script>
</body>
</html>
'''

        @app.route('/')
        def index():
            return render_template_string(HTML_TEMPLATE)

        @app.route('/cmd/<command>')
        def command(command):
            cmds = {
                'fwd': lambda: self.pico.walk(50, 0),
                'back': lambda: self.pico.walk(-50, 0),
                'left': lambda: self.pico.walk(0, 50),
                'right': lambda: self.pico.walk(0, -50),
                'tl': lambda: self.pico.turn(30),
                'tr': lambda: self.pico.turn(-30),
                'stop': self.pico.stop,
                'boot': self.pico.boot,
                'shutdown': self.pico.shutdown,
            }
            if command in cmds:
                result = cmds[command]()
                return jsonify({'status': 'ok', 'result': result})
            return jsonify({'status': 'error', 'message': 'unknown command'})

        @app.route('/gait/<gait>')
        def set_gait(gait):
            result = self.pico.set_gait(gait)
            return jsonify({'status': 'ok', 'result': result})

        @app.route('/height/<int:height>')
        def set_height(height):
            result = self.pico.set_height(height)
            return jsonify({'status': 'ok', 'result': result})

        @app.route('/status')
        def status():
            self.pico.update_sensors()
            time.sleep(0.1)  # Wait for responses
            return jsonify({
                'imu': self.pico.last_imu,
                'dist': self.pico.last_dist,
                'bat': self.pico.last_bat,
            })

        @app.route('/video_feed')
        def video_feed():
            def generate():
                import cv2
                while True:
                    if self.camera:
                        frame = self.camera.capture_frame()
                        if frame is not None:
                            _, jpeg = cv2.imencode('.jpg', frame)
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' +
                                   jpeg.tobytes() + b'\r\n')
                    time.sleep(0.1)

            return Response(generate(),
                          mimetype='multipart/x-mixed-replace; boundary=frame')

        self.app = app
        return app

    def run(self, host='0.0.0.0'):
        """Run web server."""
        if not self.app:
            self.create_app()
        print(f"Starting web server on http://{host}:{self.port}")
        self.app.run(host=host, port=self.port, threaded=True)


def main():
    """Main entry point for Zero controller."""
    print("Hexapod Zero Controller")
    print("=" * 40)

    # Connect to Pico
    pico = PicoInterface()
    if not pico.connect():
        print("Failed to connect to Pico. Exiting.")
        return

    # Initialize camera
    camera = CameraProcessor()
    camera.start()

    # Start web controller
    web = WebController(pico, camera)

    try:
        web.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        camera.stop()
        pico.disconnect()


if __name__ == '__main__':
    main()
