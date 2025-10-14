import cv2
import numpy as np

class ImagePreprocessor:
    """영상 프레임의 품질을 개선하기 위한 전처리 클래스"""

    def improve_illumination(self, frame):
        """CLAHE를 사용하여 조도를 개선하고 대비를 높입니다."""
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l_channel)
        merged = cv2.merge([cl, a_channel, b_channel])
        enhanced_frame = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
        return enhanced_frame

    def reduce_noise(self, frame):
        """Median Blur로 노이즈를 감소"""
        # 노이즈 제거 필터 강도 약간 증가 (작은 훼손 복원에도 도움)
        denoised_frame = cv2.medianBlur(frame, 5) # 3 -> 5로 변경
        return denoised_frame

    def sharpen_image(self, frame):
        """Sharpening Kernel로 블러 개선"""
        kernel = np.array([[0, -1, 0],
                           [-1, 5, -1],
                           [0, -1, 0]])
        sharpened_frame = cv2.filter2D(frame, -1, kernel)
        return sharpened_frame

    def binarize_image(self, frame):
        """Adaptive Thresholding으로 이미지를 선명한 흑백으로 변환합니다."""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # ---  이진화 파라미터 튜닝: 오탐지 감소 & 정보 보존 노력  ---
        # block_size를 키워 주변 픽셀을 더 넓게 고려 -> 노이즈 및 빛 반사에 덜 민감
        block_size = 15 # 21 -> 31 또는 41로 변경 시도
        # C 값을 약간 줄여 너무 공격적인 흑백화를 완화 -> 훼손 정보 보존
        C = 7           # 5 -> 3으로 변경 시도 (너무 낮추면 QR 자체의 대비가 약해질 수 있음)
        # ---
        
        binary_frame = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                           cv2.THRESH_BINARY, block_size, C)
        return cv2.cvtColor(binary_frame, cv2.COLOR_GRAY2BGR)

    def repair_qr_structure(self, frame):
        """
        모폴로지 '닫힘' 연산으로 QR코드의 끊어진 부분을 메우고 구조를 복원합니다.
        이 함수는 이진화된 이미지를 입력받는 것을 전제로 합니다.
        """
        # ---  모폴로지 커널 크기 튜닝: 훼손 복구 & 오탐지 억제  ---
        # 커널 크기를 (2,2) 또는 (3,3)으로 유지하면서 iterations(반복 횟수)를 추가
        # 작은 커널은 디테일 손상을 줄이고, 반복 횟수로 복원 강도 조절
        kernel = np.ones((2, 2), np.uint8) # (3,3) -> (2,2)로 변경 (더 미세하게 복원)
        
        # 반복 횟수(iterations)를 추가하여 복원 강도 조절
        # iterations=1은 한번만 적용, 2 이상이면 더 넓은 범위의 끊김 복원 가능
        repaired_frame = cv2.morphologyEx(frame, cv2.MORPH_CLOSE, kernel, iterations=1) 
        # ---
        return repaired_frame

    def preprocess_frame(self, frame):
        """전처리 파이프라인 (이진화까지만 수행)"""
        denoised_frame = self.reduce_noise(frame)
        illuminated_frame = self.improve_illumination(denoised_frame)
        final_frame = self.binarize_image(illuminated_frame)
        return final_frame