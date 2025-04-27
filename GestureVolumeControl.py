from HandTrackingModule import HandDetector
import cv2
import time
import numpy as np
import math
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Webcam setup
cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

# Hand detector
detector = HandDetector(detectionCon=0.75, maxHands=1)

# Audio control setup
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
min_vol, max_vol = volume.GetVolumeRange()[0], volume.GetVolumeRange()[1]

volBar = 400
volPer = 0
pTime = 0
volume_control_active = False

while True:
    success, img = cap.read()
    img = detector.findHands(img)
    lmList = detector.findPositions(img, draw=False)

    if len(lmList) != 0:
        # Thumb tip (id 4), Index tip (id 8), Middle tip (id 12)
        x1, y1 = lmList[4][1], lmList[4][2]
        x2, y2 = lmList[8][1], lmList[8][2]
        x3, y3 = lmList[12][1], lmList[12][2]

        # Calculate distances
        dist_thumb_index = math.hypot(x2 - x1, y2 - y1)
        dist_thumb_middle = math.hypot(x3 - x1, y3 - y1)

        # Debug visuals for fingers
        cv2.circle(img, (x1, y1), 8, (255, 0, 0), -1)  # Thumb
        cv2.circle(img, (x2, y2), 8, (0, 255, 0), -1)  # Index
        cv2.circle(img, (x3, y3), 8, (0, 0, 255), -1)  # Middle

        # Show distances on screen
        cv2.putText(img, f'Dist T-I: {int(dist_thumb_index)}', (10, 450), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)
        cv2.putText(img, f'Dist T-M: {int(dist_thumb_middle)}', (10, 470), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255), 1)

        # Toggle volume control ON (thumb close to index)
        if dist_thumb_index < 40:
            volume_control_active = True
            print("🔊 Volume Control Activated")

        # Toggle volume control OFF (thumb close to middle finger)
        elif dist_thumb_middle < 60:
            volume_control_active = False
            print("🔒 Volume Control Locked")

        if volume_control_active:
            # Volume control logic
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 2)
            cv2.circle(img, (cx, cy), 10, (255, 0, 255), -1)

            # Volume interpolation
            log_length = np.log10(dist_thumb_index + 1)
            vol = np.interp(log_length, [np.log10(30 + 1), np.log10(250 + 1)], [min_vol, max_vol])
            volBar = np.interp(dist_thumb_index, [30, 250], [400, 150])
            volPer = np.interp(dist_thumb_index, [30, 250], [0, 100])

            volume.SetMasterVolumeLevel(vol, None)

            if dist_thumb_index < 30:
                cv2.circle(img, (cx, cy), 10, (0, 255, 0), -1)

    # Volume bar UI
    cv2.rectangle(img, (50, 150), (85, 400), (0, 255, 0), 2)
    cv2.rectangle(img, (50, int(volBar)), (85, 400), (0, 255, 0), -1)
    cv2.putText(img, f'{int(volPer)} %', (40, 130), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)

    # Visual feedback for control state
    if volume_control_active:
        cv2.putText(img, "Volume Control: ON", (370, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    else:
        cv2.putText(img, "Volume Control: LOCKED", (350, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    # FPS
    cTime = time.time()
    fps = 1 / (cTime - pTime)
    pTime = cTime
    cv2.putText(img, f'FPS: {int(fps)}', (20, 40), cv2.FONT_HERSHEY_PLAIN, 2, (100, 255, 100), 2)

    # Show image
    cv2.imshow("Hand Volume Control", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
cap.release()
cv2.destroyAllWindows()
