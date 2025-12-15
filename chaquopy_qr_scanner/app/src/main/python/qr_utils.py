"""
QR 코드 처리 유틸리티 (Python)
Chaquopy를 통해 Android에서 실행됩니다.
"""

import cv2
import numpy as np

def decode_qr_opencv(image_array):
    """
    OpenCV를 사용하여 QR 코드 해독
    
    Args:
        image_array: numpy 배열 (BGR 형식)
    
    Returns:
        str: 해독된 QR 코드 텍스트, 없으면 None
    """
    try:
        # QRCodeDetector 생성
        qr_detector = cv2.QRCodeDetector()
        
        # 그레이스케일 변환
        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY)
        else:
            gray = image_array
        
        # QR 코드 감지 및 해독
        retval, decoded_info, points, straight_qrcode = qr_detector.detectAndDecodeMulti(gray)
        
        if retval and decoded_info:
            return decoded_info[0]
        
        return None
    except Exception as e:
        print(f"OpenCV QR decode error: {e}")
        return None


def preprocess_image(image_array, brightness=0, contrast=1.0):
    """
    이미지 전처리 (밝기, 대비 조정)
    
    Args:
        image_array: numpy 배열
        brightness: 밝기 조정 (-1.0 ~ 1.0)
        contrast: 대비 조정 (0.5 ~ 2.0)
    
    Returns:
        numpy 배열: 전처리된 이미지
    """
    try:
        result = image_array.copy()
        
        # 밝기 조정
        if brightness != 0:
            result = cv2.convertScaleAbs(result, alpha=1, beta=brightness * 50)
        
        # 대비 조정
        if contrast != 1.0:
            result = cv2.convertScaleAbs(result, alpha=contrast, beta=0)
        
        return result
    except Exception as e:
        print(f"Image preprocessing error: {e}")
        return image_array


def extract_roi(image_array, x, y, width, height):
    """
    ROI (Region of Interest) 추출
    
    Args:
        image_array: numpy 배열
        x: ROI 시작 X (비율 0.0 ~ 1.0)
        y: ROI 시작 Y (비율 0.0 ~ 1.0)
        width: ROI 너비 (비율 0.0 ~ 1.0)
        height: ROI 높이 (비율 0.0 ~ 1.0)
    
    Returns:
        numpy 배열: 추출된 ROI
    """
    try:
        h, w = image_array.shape[:2]
        x1 = int(x * w)
        y1 = int(y * h)
        x2 = int((x + width) * w)
        y2 = int((y + height) * h)
        
        roi = image_array[y1:y2, x1:x2]
        return roi
    except Exception as e:
        print(f"ROI extraction error: {e}")
        return image_array

