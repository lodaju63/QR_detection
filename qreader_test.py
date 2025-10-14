import cv2
from qreader import QReader
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np # numpy import는 그대로 유지합니다.

# 1. QReader 객체를 생성합니다.
qreader = QReader()

# 2. QR 코드가 있는 이미지를 불러옵니다.
image_path = "data/iPhone/250723_test/i_10_L_9.jpg" # 실제 경로를 입력해주세요.

try:
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        print(f"오류: 이미지를 로드할 수 없습니다. 파일 손상 또는 경로 문제: '{image_path}'")
        exit()
    image_for_pil = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
except cv2.error:
    print(f"오류: '{image_path}' 파일을 찾을 수 없습니다. QR 코드 이미지를 폴더에 저장했는지 확인하세요.")
    exit()

# 3. detect_and_decode 함수로 QR 코드를 찾아 내용과 위치를 디코딩합니다.
decoded_texts, detections = qreader.detect_and_decode(image=image_for_pil, return_detections=True)

# 시각화를 위한 이미지 준비: Pillow Image 객체로 변환
pil_image = Image.fromarray(image_for_pil)
draw = ImageDraw.Draw(pil_image)

# 한글 폰트 설정 (폰트 파일 경로와 크기를 지정해주세요)
# 예시: Windows 환경의 맑은 고딕
font_path = "C:/Windows/Fonts/malgun.ttf"
font_size = 30 # 폰트 크기
try:
    font = ImageFont.truetype(font_path, font_size)
except IOError:
    print(f"경고: 폰트 파일 '{font_path}'을(를) 찾을 수 없습니다. 기본 폰트를 사용합니다.")
    font = ImageFont.load_default()

# 4. 결과를 출력하고 이미지에 경계 상자 및 해독된 텍스트를 표시합니다.
if decoded_texts:
    success_count = 0
    for i, (text, detection) in enumerate(zip(decoded_texts, detections)):
        if detection and 'bbox_xyxy' in detection:
            x1, y1, x2, y2 = [int(v) for v in detection['bbox_xyxy']]
            
            # 터미널에 출력할 위치 정보 계산
            x, y, w, h = x1, y1, (x2 - x1), (y2 - y1)
            
            # 경계 상자를 Pillow 이미지 위에 그리기 (초록색)
            draw.rectangle([(x1, y1), (x2, y2)], outline=(0, 255, 0), width=2)

            display_text = ""
            if text is not None:
                display_text = f"코드 #{i+1}: {text}"
                print(f"QR 코드 인식 성공 (코드 #{i+1}): {text}")
                print(f"  위치 (px): x={x}, y={y}, width={w}, height={h}")
                success_count += 1
            else:
                display_text = f"코드 #{i+1}: 해독 실패"
                print(f"QR 코드 해독 실패 (코드 #{i+1})")
                print(f"  탐지된 위치 (px): x={x}, y={y}, width={w}, height={h}")
            
            # 해독된 텍스트를 Pillow 이미지 위에 표시 (한글 지원)
            text_color = (255, 0, 0) # RGB: 빨간색
            
            # 텍스트의 바운딩 박스 계산: font.getbbox() 사용 (Pillow 9+ 버전 권장)
            # 반환값 (left, top, right, bottom)
            # 우리는 높이만 필요하므로 bottom-top으로 계산하거나, 편의상 마지막 값을 사용합니다.
            _, _, _, text_height_val = font.getbbox(display_text)
            
            # 텍스트가 QR 코드 상단에 위치하도록 Y 좌표를 조정합니다.
            # 이미지 상단을 벗어나지 않도록 조정
            text_pos_y = max(5, y1 - text_height_val - 5)
            
            draw.text((x1, text_pos_y), display_text, font=font, fill=text_color)

        else:
            if text is not None:
                print(f"QR 코드 인식 성공 (코드 #{i+1}): {text} (위치 정보 없음)")
                success_count += 1
            else:
                print(f"QR 코드 해독 실패 (코드 #{i+1}) (위치 정보 없음)")
    
    if success_count == 0:
        print("QR 코드를 탐지했지만, 해독에는 모두 실패했습니다.")
else:
    print("QR 코드를 인식하지 못했습니다.")

# Pillow 이미지를 다시 OpenCV 이미지(BGR 채널)로 변환하여 저장
output_image_bgr = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

# 경계 상자 및 텍스트가 표시된 이미지를 파일로 저장
output_path = "output_image_with_qr_info_korean.jpg"
cv2.imwrite(output_path, output_image_bgr)
print(f"\n경계 상자와 한글 해독 정보가 표시된 이미지가 '{output_path}'로 저장되었습니다.")

# (선택 사항) 화면에 이미지 표시
# cv2.imshow("Detected QR Codes with Korean Info", output_image_bgr)
# cv2.waitKey(0)
# cv2.destroyAllWindows()