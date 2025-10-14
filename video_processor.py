import cv2
import os
import numpy as np
from image_preprocessor import ImagePreprocessor

class VideoProcessor:
    """영상 파일 처리 및 QR코드 인식 프로세스 관리"""
    def __init__(self, video_path, qr_decoder, data_manager):
        """의존성 주입 및 초기화"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"오류: '{video_path}' 파일을 찾을 수 없습니다.")
        self.video_path = video_path
        self.qr_decoder = qr_decoder
        self.data_manager = data_manager
        self.cap = cv2.VideoCapture(video_path)
        
        # 1. 전처리기 인스턴스 생성
        self.preprocessor = ImagePreprocessor()

    def process_video(self):
        """영상 처리 및 QR코드 인식 메인 루프"""
        if not self.cap.isOpened():
            print(f"오류: '{self.video_path}' 영상을 열 수 없습니다.")
            return

        video_id = self.data_manager.add_video(os.path.abspath(self.video_path))
        print(f"'{os.path.basename(self.video_path)}' 영상 처리를 시작합니다...")

        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break

            # 2. 프레임 전처리 적용
            preprocessed_frame = self.preprocessor.preprocess_frame(frame)

            timestamp = self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            
            # 3. 전처리된 프레임으로 QR코드 탐지
            qr_results = self.qr_decoder.decode_from_frame(preprocessed_frame)

            if qr_results:
                print(f"[{timestamp:.2f}s] QR Code Decoded: {[res['data'] for res in qr_results]}")
                frame_id = self.data_manager.add_frame(video_id, timestamp)
                for result in qr_results:
                    self.data_manager.add_qr_code(frame_id, result, timestamp)
                    # 원본 프레임에 결과 텍스트를 표시
                    self._draw_results(frame, result)
            
            # 4. 원본과 전처리 영상을 나란히 표시
            # 두 영상의 높이를 맞추기
            h1, w1, _ = frame.shape
            h2, w2, _ = preprocessed_frame.shape
            if h1 != h2:
                # 높이가 다를 경우 작은 쪽에 맞춰 리사이즈 (일반적으로는 크기가 같음)
                min_h = min(h1, h2)
                frame = cv2.resize(frame, (int(w1 * min_h / h1), min_h))
                preprocessed_frame = cv2.resize(preprocessed_frame, (int(w2 * min_h / h2), min_h))

            combined_view = np.hstack((frame, preprocessed_frame))
            cv2.imshow('Original vs. Preprocessed - Press Q to quit', combined_view)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.cap.release()
        cv2.destroyAllWindows()
        print("영상 처리가 완료되었습니다.")

    def _draw_results(self, frame, result):
        """인식된 QR코드 텍스트를 화면 좌측 상단에 표시"""
        data = result.get('data')
        if data:
            label = f"Decoded: {data}"
            cv2.putText(frame, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)