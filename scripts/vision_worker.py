"""Optional CPU people-count baseline. No gender, emotion, SOS or scream inference."""
import argparse
import json
import os
import time
import urllib.request


def main():
    import cv2
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default='0', help='Local video path or USB camera index; do not pass untrusted URLs')
    parser.add_argument('--camera-id', type=int, required=True)
    parser.add_argument('--server', default='http://127.0.0.1:8080')
    args = parser.parse_args()
    token = os.environ.get('DEVICE_TOKEN')
    if not token:
        parser.error('Set DEVICE_TOKEN in the environment')
    capture = cv2.VideoCapture(int(args.source) if args.source.isdigit() else args.source)
    if not capture.isOpened():
        raise SystemExit('Could not open source')
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    last = 0.0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            height, width = frame.shape[:2]
            frame = cv2.resize(frame, (640, max(128, int(height * 640 / width))))
            boxes, _ = hog.detectMultiScale(frame, winStride=(8, 8), padding=(8, 8), scale=1.05)
            for x, y, w, h in boxes:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (90, 200, 130), 2)
            if time.monotonic() - last > 3:
                payload = json.dumps({'camera_id': args.camera_id, 'people': len(boxes)}).encode()
                req = urllib.request.Request(args.server.rstrip('/')+'/api/observations', data=payload, headers={'Content-Type':'application/json', 'Authorization':'Bearer '+token})
                try:
                    with urllib.request.urlopen(req, timeout=5) as response:
                        print(response.read().decode())
                except Exception as e:
                    print('Observation not delivered:', type(e).__name__)
                last = time.monotonic()
            cv2.imshow('Her TechArmor | CPU people-count baseline | Q to exit', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        capture.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
