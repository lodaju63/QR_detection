import cv2
from qreader import QReader

# QReader 객체 생성
qreader = QReader(model_size = 'l', reencode_to = 'utf-8')

# 웹캠 또는 동영상 파일 열기
# 웹캠의 경우: cap = cv2.VideoCapture(0)
cap = cv2.VideoCapture('data/video/IMG_6211.MOV')

while cap.isOpened():
    # 프레임 읽기
    ret, frame = cap.read()
    if not ret:
        break

    # BGR 이미지를 RGB로 변환 (QReader는 RGB 이미지를 사용)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # QReader를 사용하여 QR 코드 탐지 및 해독
    decoded_qrs = qreader.detect_and_decode(image=rgb_frame)

    # 결과가 있는 경우 처리
    if decoded_qrs:
        for qr in decoded_qrs:
            print(f"QR 코드 내용: {qr}")
            # (선택 사항) 인식된 QR 코드에 경계 상자 그리기
            # bbox = ... (QReader에서 bbox 정보 얻기)
            # cv2.rectangle(...)

    # 화면에 영상 표시
    cv2.imshow('QR Code Reader', frame)

    # 'q' 키를 누르면 종료
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 자원 해제
cap.release()
cv2.destroyAllWindows()