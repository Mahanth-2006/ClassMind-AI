from cv2 import cuda
import cv2
import mediapipe as mp
import numpy as np
import time
import csv
import os

# --- Configuration & Thresholds ---
EAR_THRESHOLD = 0.22      # Eye Aspect Ratio threshold (below this = blink/closed eye)
SCREEN_YAW_LIMIT = 20.0   # Looking left/right beyond 20° means looking away
SCREEN_PITCH_LIMIT = 15.0 # Looking up/down beyond 15° means looking away

# --- MediaPipe Landmark Indices ---
# Standard 6-point eye contours for EAR calculation
LEFT_EYE = [362, 385, 387, 263, 373, 380]
RIGHT_EYE = [33, 160, 158, 133, 153, 144]

# Generic 3D reference model points for head pose estimation (in camera coordinate frame:
# +X points right, +Y points down towards chin, +Z points away from camera into the scene)
MODEL_POINTS_3D = np.array([
    (0.0, 0.0, 0.0),          # Nose tip (landmark 1)
    (0.0, 330.0, 65.0),       # Chin (landmark 152)
    (-225.0, -170.0, 135.0),  # Right eye outer corner / image left (landmark 33)
    (225.0, -170.0, 135.0),   # Left eye outer corner / image right (landmark 263)
    (-150.0, 150.0, 125.0),   # Right mouth corner / image left (landmark 61)
    (150.0, 150.0, 125.0)     # Left mouth corner / image right (landmark 291)
], dtype=np.float64)

# Corresponding landmark indices from MediaPipe Face Mesh
LANDMARK_IDS_POSE = [1, 152, 33, 263, 61, 291]


def calculate_ear(landmarks, eye_indices, img_w, img_h):
    """Calculates Eye Aspect Ratio (EAR) using Euclidean distances."""
    points = [
        np.array([
            landmarks[i].x * img_w,
            landmarks[i].y * img_h
        ])
        for i in eye_indices
    ]

    # Vertical distances
    v1 = np.linalg.norm(points[1] - points[5])
    v2 = np.linalg.norm(points[2] - points[4])

    # Horizontal distance
    h = np.linalg.norm(points[0] - points[3])

    if h == 0:
        return 0.0

    return (v1 + v2) / (2.0 * h)


def estimate_head_pose(landmarks, img_w, img_h):
    """Estimates Yaw, Pitch, and Roll angles via OpenCV solvePnP."""
    image_points = np.array([
        (landmarks[idx].x * img_w, landmarks[idx].y * img_h)
        for idx in LANDMARK_IDS_POSE
    ], dtype=np.float64)

    # Approximate camera matrix assuming center focal point
    focal_length = img_w
    center = (img_w / 2.0, img_h / 2.0)

    cam_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1]
    ], dtype=np.float64)

    dist_coeffs = np.zeros((4, 1), dtype=np.float64)

    success, rot_vec, _ = cv2.solvePnP(
        MODEL_POINTS_3D,
        image_points,
        cam_matrix,
        dist_coeffs,
        flags=cv2.SOLVEPNP_ITERATIVE
    )

    if not success:
        return 0.0, 0.0, 0.0

    rot_mat, _ = cv2.Rodrigues(rot_vec)
    angles, _, _, _, _, _ = cv2.RQDecomp3x3(rot_mat)

    pitch, yaw, roll = angles[0], angles[1], angles[2]

    return yaw, pitch, roll


def check_hand_raised(hand_landmarks, face_landmarks=None, gesture_name="None"):
    """
    Checks if a hand is raised in an online classroom posture.

    Rule:
    1. Wrist is sufficiently above face/nose level (if face landmarks available)
       or in the upper portion of the frame (if face not detected).
    2. Fingertips are pointing upward (middle fingertip above wrist).
    3. Hand is open (MediaPipe Open_Palm gesture recognized or open fingers).
    """
    wrist = hand_landmarks[0]
    middle_tip = hand_landmarks[12]

    # Hand must be oriented upright (fingertips above wrist in image coordinates)
    fingers_upright = middle_tip.y < wrist.y

    # Position rule: wrist above nose level if face is present, else upper half of screen
    if face_landmarks is not None:
        nose_y = face_landmarks[1].y
        wrist_above_face = wrist.y < nose_y
    else:
        wrist_above_face = wrist.y < 0.5

    # Open hand condition: MediaPipe Open_Palm gesture or fingers extended upward
    is_open = (gesture_name == "Open_Palm") or (
        hand_landmarks[8].y < hand_landmarks[6].y and
        hand_landmarks[12].y < hand_landmarks[10].y and
        hand_landmarks[16].y < hand_landmarks[14].y
    )

    return wrist_above_face and fingers_upright and is_open


def main():
    face_model_path = "ai_engine/models/face_landmarker.task"
    gesture_model_path = "ai_engine/models/gesture_recognizer.task"

    if not os.path.exists(face_model_path):
        print("Error: Face landmarker model not found.")
        print("Expected:", face_model_path)
        return

    if not os.path.exists(gesture_model_path):
        print("Error: Gesture recognizer model not found.")
        print("Expected:", gesture_model_path)
        print("Please download it from:")
        print("https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task")
        return

    # MediaPipe 1.0.1 uses the Tasks API instead of the older
    # mp.solutions interface.
    BaseOptions = mp.tasks.BaseOptions
    FaceLandmarker = mp.tasks.vision.FaceLandmarker
    FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
    GestureRecognizer = mp.tasks.vision.GestureRecognizer
    GestureRecognizerOptions = mp.tasks.vision.GestureRecognizerOptions
    RunningMode = mp.tasks.vision.RunningMode

    face_landmarker_options = FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=face_model_path),
        running_mode=RunningMode.VIDEO,
        num_faces=1,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        min_tracking_confidence=0.5
    )

    face_landmarker = FaceLandmarker.create_from_options(
        face_landmarker_options
    )

    gesture_recognizer_options = GestureRecognizerOptions(
        base_options=BaseOptions(model_asset_path=gesture_model_path),
        running_mode=RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5
    )

    gesture_recognizer = GestureRecognizer.create_from_options(
        gesture_recognizer_options
    )

    # Initialize Webcam with native 16:9 widescreen resolution
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    if not cap.isOpened():
        print("Error: Could not access webcam.")
        face_landmarker.close()
        gesture_recognizer.close()
        return

    # Prepare CSV Output
    csv_file = open("features.csv", mode="w", newline="")
    csv_writer = csv.writer(csv_file)

    csv_writer.writerow([
        "timestamp",
        "face_present",
        "left_ear",
        "right_ear",
        "avg_ear",
        "blink",
        "head_yaw",
        "head_pitch",
        "head_roll",
        "head_facing_screen",
        "gesture",
        "gesture_confidence",
        "hand_raised"
    ])

    start_time = time.time()
    last_timestamp_ms = 0

    # Event tracking and debouncing state to avoid duplicate continuous triggers
    thumbs_up_active = False
    thumbs_up_cooldown = 0
    hand_raised_active = False
    hand_raised_cooldown = 0

    # Explicitly create resizable window with aspect ratio preservation
    cv2.namedWindow(
        "ClassMind AI - Feature Stream",
        cv2.WINDOW_NORMAL
    )
    cv2.setWindowProperty(
        "ClassMind AI - Feature Stream",
        cv2.WND_PROP_ASPECT_RATIO,
        cv2.WINDOW_KEEPRATIO
    )

    print(
        "Capturing features... Look at the camera. "
        "Press 'q' inside the video window to stop."
    )

    try:
        while cap.isOpened():
            ret, frame = cap.read()

            if not ret:
                break

            current_time = time.time() - start_time
            h, w, _ = frame.shape

            # Convert BGR to RGB for MediaPipe processing
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # MediaPipe's Tasks API uses an Image object instead of
            # passing the OpenCV frame directly to the model.
            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb_frame
            )

            # VIDEO mode requires strictly monotonically increasing timestamp in milliseconds
            timestamp_ms = int(current_time * 1000)
            if timestamp_ms <= last_timestamp_ms:
                timestamp_ms = last_timestamp_ms + 1
            last_timestamp_ms = timestamp_ms

            # 1. Run Face Landmarker
            results = face_landmarker.detect_for_video(
                mp_image,
                timestamp_ms
            )

            # 2. Run Gesture Recognizer
            gesture_results = gesture_recognizer.recognize_for_video(
                mp_image,
                timestamp_ms
            )

            # Process hand gestures and raised hand
            # Only "Thumb_Up" is recognized/displayed; other gestures default to "None"
            current_gesture = "None"
            current_confidence = None
            hand_raised = 0

            if gesture_results.gestures:
                for i, hand_gestures in enumerate(gesture_results.gestures):
                    hand_landmarks = (
                        gesture_results.hand_landmarks[i]
                        if i < len(gesture_results.hand_landmarks)
                        else None
                    )
                    top_category = hand_gestures[0] if hand_gestures else None

                    g_name = top_category.category_name if top_category else "None"
                    g_score = top_category.score if top_category else 0.0

                    # Check for Thumbs Up (only allowed gesture)
                    if g_name == "Thumb_Up":
                        current_gesture = "Thumb_Up"
                        current_confidence = g_score

                    # Check for Hand Raised (uses g_name internally for Open_Palm, without exposing it)
                    if hand_landmarks is not None:
                        face_pts = results.face_landmarks[0] if results.face_landmarks else None
                        if check_hand_raised(hand_landmarks, face_pts, g_name):
                            hand_raised = 1

            # Event debouncing and state management
            is_thumbs_up = (current_gesture == "Thumb_Up")

            # Debounce Thumbs Up event: trigger once when gesture appears, don't re-trigger while held
            if is_thumbs_up:
                thumbs_up_cooldown = 0
                if not thumbs_up_active:
                    thumbs_up_active = True
                    conf_str = f"{current_confidence:.2f}" if current_confidence is not None else "N/A"
                    print(f"[{round(current_time, 2)}s] Event: Thumbs Up detected (Confidence: {conf_str})")
            else:
                thumbs_up_cooldown += 1
                if thumbs_up_cooldown >= 5:
                    thumbs_up_active = False

            # Debounce Hand Raised event: trigger once when hand is raised, don't re-trigger while held
            if hand_raised:
                hand_raised_cooldown = 0
                if not hand_raised_active:
                    hand_raised_active = True
                    print(f"[{round(current_time, 2)}s] Event: Hand Raised detected")
            else:
                hand_raised_cooldown += 1
                if hand_raised_cooldown >= 5:
                    hand_raised_active = False

            if results.face_landmarks:
                landmarks = results.face_landmarks[0]

                # 1. Blink Calculation
                ear_l = calculate_ear(
                    landmarks,
                    LEFT_EYE,
                    w,
                    h
                )

                ear_r = calculate_ear(
                    landmarks,
                    RIGHT_EYE,
                    w,
                    h
                )

                avg_ear = (ear_l + ear_r) / 2.0

                blink = 1 if avg_ear < EAR_THRESHOLD else 0

                # 2. Head Orientation
                yaw, pitch, roll = estimate_head_pose(
                    landmarks,
                    w,
                    h
                )

                # 3. Head Orientation Flag
                # head_facing_screen indicates head orientation toward the screen.
                # It is not eye-gaze estimation.
                head_facing_screen = 1 if (
                    abs(yaw) < SCREEN_YAW_LIMIT and
                    abs(pitch) < SCREEN_PITCH_LIMIT
                ) else 0

                row = [
                    round(current_time, 2),
                    1,
                    round(ear_l, 4),
                    round(ear_r, 4),
                    round(avg_ear, 4),
                    blink,
                    round(yaw, 2),
                    round(pitch, 2),
                    round(roll, 2),
                    head_facing_screen,
                    current_gesture,
                    round(current_confidence, 4) if current_confidence is not None else None,
                    hand_raised
                ]

            else:
                # Student out of frame
                row = [
                    round(current_time, 2),
                    0,
                    None,
                    None,
                    None,
                    0,
                    None,
                    None,
                    None,
                    0,
                    current_gesture,
                    round(current_confidence, 4) if current_confidence is not None else None,
                    hand_raised
                ]

            csv_writer.writerow(row)

            # Draw telemetry on screen
            ear_disp = f"{row[4]:.2f}" if row[4] is not None else "None"
            status = (
                f"Face: {row[1]} | "
                f"Yaw: {row[6]} | "
                f"Pitch: {row[7]} | "
                f"EAR: {ear_disp} | "
                f"Blink: {row[5]} | "
                f"Head: {row[9]}"
            )

            cv2.putText(
                frame,
                status,
                (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 0),
                2
            )

            if current_gesture == "Thumb_Up" and current_confidence is not None:
                gesture_text = f"Gesture: Thumb_Up ({current_confidence:.2f})"
            else:
                gesture_text = "Gesture: None"

            gesture_status = (
                f"{gesture_text} | "
                f"Hand Raised: {'Yes' if hand_raised else 'No'}"
            )

            cv2.putText(
                frame,
                gesture_status,
                (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 0),
                2
            )

            cv2.imshow(
                "ClassMind AI - Feature Stream",
                frame
            )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        csv_file.close()
        face_landmarker.close()
        gesture_recognizer.close()

        print(
            "Feature logging completed. "
            "Results saved to features.csv"
        )


if __name__ == "__main__":
    main()