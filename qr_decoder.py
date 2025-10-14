# qr_decoder.py

from qreader import QReader
import cv2
import numpy as np
from image_preprocessor import ImagePreprocessor

class QRDecoder:
    """
    모든 탐지/해독 전략을 통합하고 결과를 지능적으로 병합하는 최종 디코더.
    """
    
    def __init__(self):
        """탐지기 및 해독기 인스턴스 초기화"""
        self.qreader = QReader(model_size='s', min_confidence=0.7, reencode_to='utf-8')
        self.detector = cv2.QRCodeDetector()
        self.preprocessor = ImagePreprocessor()

    def _get_iou(self, boxA, boxB):
        """두 바운딩 박스 간의 IoU (Intersection over Union)를 계산합니다."""
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        # ---
        interArea = max(0, xB - xA) * max(0, yB - yA)
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        iou = interArea / float(boxAArea + boxBArea - interArea) if (boxAArea + boxBArea - interArea) > 0 else 0
        return iou

    def _merge_results(self, existing_results, new_results, iou_threshold=0.7):
        """새로운 결과를 기존 결과에 병합하고, 더 좋은 결과로 업데이트합니다."""
        merged = list(existing_results)

        for new_res in new_results:
            is_duplicate = False
            for i, existing_res in enumerate(merged):
                if new_res['data'] and new_res['data'] == existing_res['data']:
                    is_duplicate = True
                    if existing_res['status'] == 'FAILED_DECODING' and new_res['status'] == 'SUCCESS':
                        merged[i] = new_res
                    break
                if new_res['location'] is not None and existing_res['location'] is not None:
                    if self._get_iou(new_res['location'], existing_res['location']) > iou_threshold:
                        is_duplicate = True
                        if existing_res['status'] == 'FAILED_DECODING' and new_res['status'] == 'SUCCESS':
                            merged[i] = new_res
                        break
            
            if not is_duplicate:
                merged.append(new_res)
        
        return merged

    def _format_qreader_results(self, decoded_qrs, detections):
        """QReader 결과를 표준 형식으로 변환"""
        results = []
        if not decoded_qrs: return results
        for text, detection in zip(decoded_qrs, detections):
            results.append({
                'data': text,
                'location': detection.get('bbox_xyxy', None),
                'status': 'SUCCESS' if text else 'FAILED_DECODING'
            })
        return results

    def decode_from_frame(self, frame_bgr):
        """통합 하이브리드 전략으로 프레임에서 QR코드 정보 추출."""
        final_results = []

        # --- 전략 1: QReader - 원본 이미지 ---
        rgb_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        d, det = self.qreader.detect_and_decode(image=rgb_frame, return_detections=True)
        final_results = self._merge_results(final_results, self._format_qreader_results(d, det))

        # --- 전략 2: QReader - CLAHE ---
        illuminated = self.preprocessor.improve_illumination(frame_bgr)
        illuminated_rgb = cv2.cvtColor(illuminated, cv2.COLOR_BGR2RGB)
        d, det = self.qreader.detect_and_decode(image=illuminated_rgb, return_detections=True)
        final_results = self._merge_results(final_results, self._format_qreader_results(d, det))

        # --- 전략 3: OpenCV 탐지 후 교정 + QReader 해독 ---
        retval, decoded_info, points, straight_qrcode = self.detector.detectAndDecodeMulti(frame_bgr)
        if retval and points is not None:
            opencv_results = []
            for i, point_set in enumerate(points):
                if point_set is None or len(point_set) != 4: continue
                
                rectified = self._four_point_transform(frame_bgr, point_set)
                if rectified.shape[0] < 50 or rectified.shape[1] < 50:
                    rectified = cv2.resize(rectified, (100, 100), interpolation=cv2.INTER_CUBIC)
                
                rectified_rgb = cv2.cvtColor(rectified, cv2.COLOR_BGR2RGB)
                d_rect, det_rect = self.qreader.detect_and_decode(image=rectified_rgb, return_detections=True)
                
                qr_data = d_rect[0] if d_rect and d_rect[0] else None
                opencv_results.append({
                    'data': qr_data,
                    'location': self._points_to_bbox(point_set),
                    'status': 'SUCCESS' if qr_data else 'FAILED_DECODING'
                })
            final_results = self._merge_results(final_results, opencv_results)

        # --- 전략 4: QReader - 모폴로지 복원 ---
        binarized = self.preprocessor.preprocess_frame(frame_bgr)
        repaired = self.preprocessor.repair_qr_structure(binarized)
        repaired_rgb = cv2.cvtColor(repaired, cv2.COLOR_BGR2RGB)
        d, det = self.qreader.detect_and_decode(image=repaired_rgb, return_detections=True)
        final_results = self._merge_results(final_results, self._format_qreader_results(d, det))

        return final_results

    def _four_point_transform(self, image, pts):
        """네 꼭짓점 좌표를 받아 이미지를 반듯한 사각형으로 변환"""
        rect = np.array(pts, dtype="float32")
        (tl, tr, br, bl) = rect
        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))
        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))
        dst = np.array([[0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]], dtype="float32")
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
        return warped

    def _points_to_bbox(self, points):
        """OpenCV 꼭짓점을 [x1, y1, x2, y2] bbox로 변환"""
        points = np.array(points, dtype=np.int32)
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        return [np.min(x_coords), np.min(y_coords), np.max(x_coords), np.max(y_coords)]