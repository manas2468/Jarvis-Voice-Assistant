"""
Jarvis Detection Mode — Real-time Object Detection via YOLOv8
==============================================================
Accepts frames from LiveKit video track (no webcam conflict).
100% local YOLO inference — no API calls.

Usage: Say "detection mode" to Jarvis while on LiveKit.
"""

import cv2
import numpy as np
import queue
import threading
import time
import logging
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("detection_mode")

_model = None
_running = False
_thread = None
_detected_objects = []
_lock = threading.Lock()
_frame_queue = queue.Queue(maxsize=3)


def _get_model():
    global _model
    if _model is None:
        logger.info("Loading YOLOv8 model...")
        _model = YOLO("yolov8n.pt")
        logger.info("YOLOv8 model loaded.")
    return _model


def feed_frame(frame_bgr):
    """Feed a BGR numpy frame from LiveKit video track."""
    try:
        if _frame_queue.full():
            _frame_queue.get_nowait()
        _frame_queue.put_nowait(frame_bgr)
    except:
        pass


def _draw_hud(frame, detections, fps):
    h, w = frame.shape[:2]
    overlay = frame.copy()

    # HUD corners
    color = (255, 229, 0)
    bk = 40
    for cx, cy, dx, dy in [(10,10,1,1),(w-10,10,-1,1),(10,h-10,1,-1),(w-10,h-10,-1,-1)]:
        cv2.line(overlay, (cx, cy), (cx+bk*dx, cy), color, 2)
        cv2.line(overlay, (cx, cy), (cx, cy+bk*dy), color, 2)

    # Title bar
    cv2.rectangle(overlay, (0, 0), (w, 38), (10, 10, 10), -1)
    cv2.putText(overlay, "J.A.R.V.I.S  DETECTION MODE", (15, 26),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 229, 255), 1, cv2.LINE_AA)
    cv2.putText(overlay, f"FPS: {fps:.0f}", (w-100, 26),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 200, 200), 1, cv2.LINE_AA)

    for det in detections:
        x1, y1, x2, y2 = det["box"]
        label, conf = det["label"], det["conf"]
        dc = (0, 255, 200)
        cv2.rectangle(overlay, (x1, y1), (x2, y2), dc, 1)
        cl = 15
        for bx, by, bdx, bdy in [(x1,y1,1,1),(x2,y1,-1,1),(x1,y2,1,-1),(x2,y2,-1,-1)]:
            cv2.line(overlay, (bx, by), (bx+cl*bdx, by), dc, 2)
            cv2.line(overlay, (bx, by), (bx, by+cl*bdy), dc, 2)
        text = f"{label} {conf:.0%}"
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(overlay, (x1, y1-th-10), (x1+tw+10, y1), (10, 10, 10), -1)
        cv2.putText(overlay, text, (x1+5, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, dc, 1, cv2.LINE_AA)

    obj_counts = {}
    for d in detections:
        obj_counts[d["label"]] = obj_counts.get(d["label"], 0) + 1
    ph = 24 + len(obj_counts) * 22
    cv2.rectangle(overlay, (w-210, 48), (w-5, 48+ph), (10, 10, 10), -1)
    cv2.putText(overlay, f"OBJECTS: {len(detections)}", (w-200, 66),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 229, 255), 1, cv2.LINE_AA)
    for i, (name, cnt) in enumerate(obj_counts.items()):
        cv2.putText(overlay, f"> {name}: {cnt}", (w-200, 88+i*22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 200, 180), 1, cv2.LINE_AA)

    cv2.rectangle(overlay, (0, h-30), (w, h), (10, 10, 10), -1)
    cv2.putText(overlay, "Press Q or ESC to exit", (15, h-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 140, 160), 1, cv2.LINE_AA)
    return overlay


def _detection_loop():
    global _running, _detected_objects
    model = _get_model()
    fps = 0
    prev = time.time()
    logger.info("Detection mode started — waiting for video frames from LiveKit")

    while _running:
        frame = None
        try:
            frame = _frame_queue.get(timeout=0.1)
        except queue.Empty:
            # Show waiting screen if no frames yet
            wait_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(wait_frame, "Waiting for camera feed from LiveKit...", (40, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 229, 255), 1, cv2.LINE_AA)
            cv2.imshow("JARVIS - Detection Mode", wait_frame)
            key = cv2.waitKey(30) & 0xFF
            if key == ord('q') or key == 27:
                break
            continue

        # Resize for consistent processing
        frame = cv2.resize(frame, (960, 540))

        # YOLO inference
        results = model(frame, verbose=False, conf=0.35)
        detections = []
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                label = model.names[int(box.cls[0])]
                conf = float(box.conf[0])
                detections.append({"box": (x1, y1, x2, y2), "label": label, "conf": conf})

        with _lock:
            _detected_objects = [d["label"] for d in detections]

        now = time.time()
        fps = 0.8 * fps + 0.2 / max(now - prev, 0.001)
        prev = now

        hud = _draw_hud(frame, detections, fps)
        cv2.imshow("JARVIS - Detection Mode", hud)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break

    cv2.destroyAllWindows()
    _running = False
    logger.info("Detection mode stopped")


def start_detection() -> str:
    global _running, _thread
    if _running:
        return "Detection mode is already active, sir."
    _running = True
    _thread = threading.Thread(target=_detection_loop, daemon=True)
    _thread.start()
    return ("Detection mode activated, sir. I am now scanning through your camera. "
            "You should see a detection window on your screen. Press Q to close it.")


def stop_detection() -> str:
    global _running
    if not _running:
        return "Detection mode is not currently active, sir."
    _running = False
    return "Detection mode deactivated, sir."


def get_detected_objects() -> list:
    with _lock:
        return list(_detected_objects)


def get_detection_summary() -> str:
    with _lock:
        objects = list(_detected_objects)
    if not objects:
        if not _running:
            return "Detection mode is not active. Say 'detection mode' to start."
        return "I don't see any recognizable objects at the moment, sir."
    counts = {}
    for obj in objects:
        counts[obj] = counts.get(obj, 0) + 1
    parts = [f"{c} {n}{'s' if c > 1 else ''}" for n, c in counts.items()]
    return f"I can currently see: {', '.join(parts)}."


def create_detection_tools():
    from livekit.agents.llm import function_tool

    @function_tool()
    async def detection_mode(action: str = "start") -> str:
        """Activates or deactivates real-time object detection using the user's camera.
        Opens a window with live bounding boxes around detected objects.
        Use when user says 'detection mode', 'start detection', 'activate detection',
        'what objects are around me', 'scan my surroundings'.
        Pass action='start' to begin or action='stop' to end."""
        if action.lower() in ("stop", "off", "end", "deactivate"):
            return stop_detection()
        return start_detection()

    @function_tool()
    async def what_do_you_see() -> str:
        """Reports what objects are currently detected in the camera feed.
        Use when user asks 'what do you see', 'what objects are there',
        'what is in front of me', 'identify objects'.
        Auto-starts detection if not running."""
        if not _running:
            start_detection()
            import asyncio
            await asyncio.sleep(2)
        return get_detection_summary()

    return [detection_mode, what_do_you_see]


if __name__ == "__main__":
    print("Standalone test: using direct webcam (not LiveKit)")
    _running = True
    model = _get_model()
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("No webcam available. Run through LiveKit agent instead.")
        exit(1)
    while True:
        ret, f = cap.read()
        if not ret:
            break
        feed_frame(f)
        try:
            frame = _frame_queue.get_nowait()
            frame = cv2.resize(frame, (960, 540))
            results = model(frame, verbose=False, conf=0.35)
            dets = []
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    dets.append({"box": (x1, y1, x2, y2),
                                 "label": model.names[int(box.cls[0])],
                                 "conf": float(box.conf[0])})
            hud = _draw_hud(frame, dets, 30)
            cv2.imshow("JARVIS Detection Test", hud)
        except:
            pass
        if cv2.waitKey(1) & 0xFF in (ord('q'), 27):
            break
    cap.release()
    cv2.destroyAllWindows()
