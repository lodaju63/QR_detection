import cv2
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import time
from batch_data import BatchTestDataManager 
from qr_decoder import QRDecoder
import shutil

# --- 설정값 (Config) ---
IMAGE_FOLDER = "C:/Users/Administrator/qrcode/data/iPhone/250723_test" 
OUTPUT_FOLDER = "C:/Users/Administrator/qrcode/output_results"
FONT_PATH = "C:/Windows/Fonts/malgun.ttf"
FONT_SIZE = 30 
EXCEL_OUTPUT_FILENAME = "batch_test_summary.xlsx"
BATCH_DB_PATH = 'batch_qr_test_temp.db'

# 이전 결과 폴더를 삭제하고 새로 생성
if os.path.exists(OUTPUT_FOLDER):
    shutil.rmtree(OUTPUT_FOLDER)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 1. QRDecoder 객체를 생성합니다.
qr_decoder = QRDecoder()

# 배치 테스트용 DataManager 인스턴스 생성
batch_data_manager = BatchTestDataManager(db_path=BATCH_DB_PATH)
# 새 테스트를 시작할 때마다 DB를 초기화
batch_data_manager.reset_database() 

# 한글 폰트 로드
try:
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
except IOError:
    print(f"경고: 폰트 파일 '{FONT_PATH}'을(를) 찾을 수 없습니다. 기본 폰트를 사용합니다.")
    font = ImageFont.load_default()

total_images_processed = 0
total_qr_detected_across_all_images = 0
total_qr_decoded_across_all_images = 0
total_processing_time = 0

# --- 이미지 폴더 순회하며 처리 ---
print(f"이미지 폴더 '{IMAGE_FOLDER}'에서 QR 코드 인식을 시작합니다.\n")
all_image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif'))]

if not all_image_files:
    print(f"'{IMAGE_FOLDER}' 폴더에 처리할 이미지 파일이 없습니다.")
    batch_data_manager.export_to_excel(EXCEL_OUTPUT_FILENAME)
    batch_data_manager.close()
    exit()

for filename in all_image_files:
    image_full_path = os.path.join(IMAGE_FOLDER, filename)
    output_image_filename = f"processed_{filename}"
    output_image_path = os.path.join(OUTPUT_FOLDER, output_image_filename)

    print(f"--- '{filename}' 처리 중 ---")
    start_time_image = time.time() 

    original_frame_bgr = None
    try:
        original_frame_bgr = cv2.imread(image_full_path) # 원본 BGR 프레임 로드
        if original_frame_bgr is None:
            print(f"오류: 이미지를 로드할 수 없습니다. 파일 손상 또는 경로 문제: '{image_full_path}'")
            continue
        
    except cv2.error:
        print(f"오류: '{image_full_path}' 파일을 찾을 수 없습니다.")
        continue

    # QRDecoder에게 원본 이미지를 전달하여 하이브리드 방식으로 디코딩을 실행합니다.
    qr_results = qr_decoder.decode_from_frame(original_frame_bgr)
    
    # 시각화는 원본 컬러 이미지를 기반으로 Pillow 객체를 생성합니다.
    pil_image = Image.fromarray(cv2.cvtColor(original_frame_bgr, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_image)

    image_qr_detected_count = len(qr_results)
    image_qr_decoded_count = sum(1 for res in qr_results if res['status'] == 'SUCCESS')
    
    qr_results_for_db = []

    if qr_results:
        for i, result in enumerate(qr_results):
            qr_data = result['data']
            qr_location = result['location']
            qr_status = result['status']
            
            qr_location_str = "N/A"
            if qr_location is not None:
                # 상태에 따라 사각형 색상 결정
                if qr_status == 'SUCCESS':
                    box_color = (0, 255, 0) # 성공: 녹색
                else:
                    box_color = (0, 0, 255) # 실패: 파란색
                
                x1, y1, x2, y2 = [int(v) for v in qr_location]
                x, y, w, h = x1, y1, (x2 - x1), (y2 - y1)
                qr_location_str = f"({x},{y},{w},{h})" 
                
                # 결정된 색상으로 경계 상자를 그립니다.
                draw.rectangle([(x1, y1), (x2, y2)], outline=box_color, width=3)

                display_text = f"코드 #{i+1}: {qr_data if qr_data else '해독 실패'}"
                
                text_color = (255, 0, 0)
                _, _, _, text_height_val = font.getbbox(display_text)
                text_pos_y = max(5, y1 - text_height_val - 5)
                
                draw.text((x1, text_pos_y), display_text, font=font, fill=text_color)
            else:
                qr_location_str = "NO_LOCATION_INFO"

            qr_results_for_db.append({
                'qr_data': qr_data,
                'qr_location': qr_location_str,
                'qr_status': qr_status
            })

    else: # QR 코드를 아예 탐지하지 못한 경우
        print(" 	QR 코드를 인식하지 못했습니다.")
        qr_results_for_db.append({
            'qr_data': None,
            'qr_location': None,
            'qr_status': "NO_QR_DETECTED"
        })

    end_time_image = time.time()
    processing_time_per_image = end_time_image - start_time_image
    total_processing_time += processing_time_per_image

    for qr_res in qr_results_for_db:
        batch_data_manager.add_test_result(
            image_file_name=filename,
            image_file_path=image_full_path,
            processed_output_image_path=output_image_path,
            qr_code_data=qr_res['qr_data'],
            qr_code_location=qr_res['qr_location'],
            qr_code_status=qr_res['qr_status'],
            processing_time_per_image=processing_time_per_image
        )
    
    output_image_bgr = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    cv2.imwrite(output_image_path, output_image_bgr)
    
    print(f" 	탐지된 QR 코드 수: {image_qr_detected_count}개")
    print(f" 	해독 성공 QR 코드 수: {image_qr_decoded_count}개")
    print(f" 	단일 이미지 처리 시간: {processing_time_per_image:.4f}초")
    print(f" 	처리된 이미지가 '{output_image_path}'으로 저장되었습니다.\n")

    total_images_processed += 1
    total_qr_detected_across_all_images += image_qr_detected_count
    total_qr_decoded_across_all_images += image_qr_decoded_count

print("\n--- 모든 이미지 처리 완료 ---")
print(f"총 처리된 이미지 파일 수: {total_images_processed}개")
print(f"총 탐지된 QR 코드 수 (전체 이미지 대상): {total_qr_detected_across_all_images}개")
print(f"총 해독 성공 QR 코드 수 (전체 이미지 대상): {total_qr_decoded_across_all_images}개")
if total_images_processed > 0:
    print(f"평균 이미지 처리 시간: {total_processing_time / total_images_processed:.4f}초/이미지")
    print(f"총 배치 처리 시간: {total_processing_time:.4f}초")
print(f"결과 이미지는 '{OUTPUT_FOLDER}' 폴더에 저장되었습니다.")

batch_data_manager.export_to_excel(EXCEL_OUTPUT_FILENAME)

batch_data_manager.close()