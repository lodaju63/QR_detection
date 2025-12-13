"""
안드로이드용 QR 코드 스캐너 (Kivy 기반)
- 후면/앞면 카메라 지원
- ROI (Region of Interest) 설정
- 카메라 하드웨어 옵션 조정 (밝기, 노출 등)
- 실시간 QR 해독
"""

import os
import sys
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.camera import Camera
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.logger import Logger
import cv2
import numpy as np

# QR 해독 라이브러리
PYZBAR_AVAILABLE = False
OPENCV_QR_AVAILABLE = False
qr_detector = None

try:
    from pyzbar import pyzbar
    PYZBAR_AVAILABLE = True
except ImportError:
    try:
        from pyzbar.pyzbar import decode as pyzbar_decode
        PYZBAR_AVAILABLE = True
        pyzbar = type('obj', (object,), {'decode': pyzbar_decode})
    except ImportError:
        PYZBAR_AVAILABLE = False
        Logger.warning("pyzbar not available, trying OpenCV QRCodeDetector")
        try:
            qr_detector = cv2.QRCodeDetector()
            OPENCV_QR_AVAILABLE = True
        except:
            OPENCV_QR_AVAILABLE = False
            Logger.error("No QR decoder available!")

# Dynamsoft (선택적)
try:
    from dynamsoft_barcode_reader_bundle import dbr, license, cvr
    DBR_AVAILABLE = True
except ImportError:
    DBR_AVAILABLE = False


class QRScannerApp(App):
    """QR 스캐너 메인 앱"""
    
    def build(self):
        self.camera = None
        self.dbr_reader = None
        self.roi_x = 0.2  # ROI 시작 X (화면 비율)
        self.roi_y = 0.2  # ROI 시작 Y
        self.roi_width = 0.6  # ROI 너비
        self.roi_height = 0.6  # ROI 높이
        self.camera_index = 0  # 0: 후면, 1: 앞면
        self.last_decoded = None
        self.scanning = False
        
        # Dynamsoft 초기화
        if DBR_AVAILABLE:
            try:
                license_key = os.environ.get(
                    'DYNAMSOFT_LICENSE_KEY',
                    't0085YQEAADYdcL2llMa8vH1Rtnun+43saE/kdAE7ZbIxMQGRMtSzVSZRI8vfOK4Ids52rjekwzh87yABFLraXw5Va1BV7NnBjI8m7qbw3kxOprI75ExJpw=='
                )
                error = license.LicenseManager.init_license(license_key)
                if error[0] == 0:
                    self.dbr_reader = cvr.CaptureVisionRouter()
                    Logger.info("Dynamsoft initialized")
            except Exception as e:
                Logger.warning(f"Dynamsoft init failed: {e}")
        
        # UI 구성
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 카메라 뷰
        self.camera_widget = Camera(
            index=self.camera_index,
            resolution=(640, 480),
            play=True
        )
        self.camera_widget.bind(on_texture=self.on_camera_frame)
        layout.add_widget(self.camera_widget)
        
        # ROI 표시용 레이블 (오버레이)
        self.roi_label = Label(
            text='',
            size_hint=(None, None),
            size=(200, 50),
            pos_hint={'center_x': 0.5, 'y': 0.9}
        )
        layout.add_widget(self.roi_label)
        
        # 결과 표시
        self.result_label = Label(
            text='QR 코드를 스캔하세요',
            size_hint_y=None,
            height=60,
            text_size=(None, None),
            halign='center'
        )
        layout.add_widget(self.result_label)
        
        # 컨트롤 패널
        controls = BoxLayout(orientation='vertical', size_hint_y=None, height=400, spacing=5)
        
        # 카메라 전환 버튼
        camera_btn = ToggleButton(
            text='후면 카메라',
            size_hint_y=None,
            height=40
        )
        camera_btn.bind(on_press=self.toggle_camera)
        controls.add_widget(camera_btn)
        
        # 스캔 시작/정지 버튼
        self.scan_btn = Button(
            text='스캔 시작',
            size_hint_y=None,
            height=40
        )
        self.scan_btn.bind(on_press=self.toggle_scan)
        controls.add_widget(self.scan_btn)
        
        # ROI 설정
        roi_label = Label(text='스캔 영역 (ROI)', size_hint_y=None, height=30)
        controls.add_widget(roi_label)
        
        # ROI X 위치
        roi_x_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        roi_x_layout.add_widget(Label(text='X:', size_hint_x=0.2))
        self.roi_x_slider = Slider(min=0, max=0.8, value=self.roi_x, size_hint_x=0.6)
        self.roi_x_slider.bind(value=self.update_roi_x)
        roi_x_layout.add_widget(self.roi_x_slider)
        controls.add_widget(roi_x_layout)
        
        # ROI Y 위치
        roi_y_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        roi_y_layout.add_widget(Label(text='Y:', size_hint_x=0.2))
        self.roi_y_slider = Slider(min=0, max=0.8, value=self.roi_y, size_hint_x=0.6)
        self.roi_y_slider.bind(value=self.update_roi_y)
        roi_y_layout.add_widget(self.roi_y_slider)
        controls.add_widget(roi_y_layout)
        
        # ROI 너비
        roi_w_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        roi_w_layout.add_widget(Label(text='너비:', size_hint_x=0.2))
        self.roi_w_slider = Slider(min=0.2, max=1.0, value=self.roi_width, size_hint_x=0.6)
        self.roi_w_slider.bind(value=self.update_roi_w)
        roi_w_layout.add_widget(self.roi_w_slider)
        controls.add_widget(roi_w_layout)
        
        # ROI 높이
        roi_h_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        roi_h_layout.add_widget(Label(text='높이:', size_hint_x=0.2))
        self.roi_h_slider = Slider(min=0.2, max=1.0, value=self.roi_height, size_hint_x=0.6)
        self.roi_h_slider.bind(value=self.update_roi_h)
        roi_h_layout.add_widget(self.roi_h_slider)
        controls.add_widget(roi_h_layout)
        
        # 카메라 설정
        camera_settings_label = Label(text='카메라 설정', size_hint_y=None, height=30)
        controls.add_widget(camera_settings_label)
        
        # 밝기 조정 (Android에서는 제한적)
        brightness_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        brightness_layout.add_widget(Label(text='밝기:', size_hint_x=0.2))
        self.brightness_slider = Slider(min=-1, max=1, value=0, size_hint_x=0.6)
        brightness_layout.add_widget(self.brightness_slider)
        controls.add_widget(brightness_layout)
        
        # 대비 조정
        contrast_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        contrast_layout.add_widget(Label(text='대비:', size_hint_x=0.2))
        self.contrast_slider = Slider(min=0.5, max=2.0, value=1.0, size_hint_x=0.6)
        contrast_layout.add_widget(self.contrast_slider)
        controls.add_widget(contrast_layout)
        
        # 노출 보정 (소프트웨어)
        exposure_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        exposure_layout.add_widget(Label(text='노출:', size_hint_x=0.2))
        self.exposure_slider = Slider(min=-2, max=2, value=0, size_hint_x=0.6)
        exposure_layout.add_widget(self.exposure_slider)
        controls.add_widget(exposure_layout)
        
        layout.add_widget(controls)
        
        # 스크롤 가능하도록
        from kivy.uix.scrollview import ScrollView
        scroll = ScrollView()
        scroll.add_widget(layout)
        
        return scroll
    
    def toggle_camera(self, instance):
        """카메라 전환 (후면/앞면)"""
        self.camera_index = 1 - self.camera_index
        self.camera_widget.index = self.camera_index
        instance.text = '앞면 카메라' if self.camera_index == 1 else '후면 카메라'
        Logger.info(f"Camera switched to index {self.camera_index}")
    
    def toggle_scan(self, instance):
        """스캔 시작/정지"""
        self.scanning = not self.scanning
        instance.text = '스캔 정지' if self.scanning else '스캔 시작'
        if not self.scanning:
            self.result_label.text = 'QR 코드를 스캔하세요'
            self.last_decoded = None
    
    def update_roi_x(self, instance, value):
        """ROI X 위치 업데이트"""
        self.roi_x = value
        self.update_roi_display()
    
    def update_roi_y(self, instance, value):
        """ROI Y 위치 업데이트"""
        self.roi_y = value
        self.update_roi_display()
    
    def update_roi_w(self, instance, value):
        """ROI 너비 업데이트"""
        self.roi_width = value
        self.update_roi_display()
    
    def update_roi_h(self, instance, value):
        """ROI 높이 업데이트"""
        self.roi_height = value
        self.update_roi_display()
    
    def update_roi_display(self):
        """ROI 표시 업데이트"""
        self.roi_label.text = f'ROI: ({self.roi_x:.1f}, {self.roi_y:.1f}) {self.roi_width:.1f}x{self.roi_height:.1f}'
    
    def on_camera_frame(self, instance):
        """카메라 프레임 처리"""
        if not self.scanning or instance.texture is None:
            return
        
        try:
            # Kivy Texture를 numpy 배열로 변환
            texture = instance.texture
            size = texture.size
            pixels = texture.pixels
            
            # RGBA를 BGR로 변환
            buf = np.frombuffer(pixels, dtype=np.uint8)
            buf = buf.reshape((size[1], size[0], 4))
            frame = cv2.cvtColor(buf, cv2.COLOR_RGBA2BGR)
            
            # ROI 영역 추출
            h, w = frame.shape[:2]
            roi_x1 = int(self.roi_x * w)
            roi_y1 = int(self.roi_y * h)
            roi_x2 = int((self.roi_x + self.roi_width) * w)
            roi_y2 = int((self.roi_y + self.roi_height) * h)
            
            roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]
            
            if roi.size == 0:
                return
            
            # 카메라 설정 적용 (소프트웨어 처리)
            brightness = self.brightness_slider.value
            contrast = self.contrast_slider.value
            exposure = self.exposure_slider.value
            
            # 밝기 조정
            if brightness != 0:
                roi = cv2.convertScaleAbs(roi, alpha=1, beta=brightness * 50)
            
            # 대비 조정
            if contrast != 1.0:
                roi = cv2.convertScaleAbs(roi, alpha=contrast, beta=0)
            
            # 노출 보정 (간단한 감마 조정)
            if exposure != 0:
                gamma = 1.0 + exposure * 0.5
                inv_gamma = 1.0 / gamma
                table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
                roi = cv2.LUT(roi, table)
            
            # QR 코드 해독
            decoded_text = self.decode_qr(roi)
            
            if decoded_text and decoded_text != self.last_decoded:
                self.last_decoded = decoded_text
                self.result_label.text = f'✅ 해독 성공:\n{decoded_text[:50]}'
                Logger.info(f"QR decoded: {decoded_text}")
        
        except Exception as e:
            Logger.error(f"Frame processing error: {e}")
    
    def decode_qr(self, roi):
        """QR 코드 해독"""
        if roi.size == 0:
            return None
        
        # Dynamsoft 우선 사용
        if self.dbr_reader:
            try:
                rgb_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
                captured_result = self.dbr_reader.capture(rgb_roi, dbr.EnumImagePixelFormat.IPF_RGB_888)
                
                items = None
                if hasattr(captured_result, 'get_decoded_barcodes_result'):
                    barcode_result = captured_result.get_decoded_barcodes_result()
                    if barcode_result:
                        items = barcode_result.get_items() if hasattr(barcode_result, 'get_items') else None
                
                if not items and hasattr(captured_result, 'items'):
                    items = captured_result.items
                
                if not items and hasattr(captured_result, 'decoded_barcodes_result'):
                    barcode_result = captured_result.decoded_barcodes_result
                    if barcode_result:
                        items = barcode_result.items if hasattr(barcode_result, 'items') else None
                
                if items and len(items) > 0:
                    barcode_item = items[0]
                    if hasattr(barcode_item, 'get_text'):
                        try:
                            return barcode_item.get_text()
                        except:
                            pass
                    if hasattr(barcode_item, 'text'):
                        try:
                            return barcode_item.text
                        except:
                            pass
            except Exception as e:
                Logger.warning(f"Dynamsoft decode error: {e}")
        
        # pyzbar 사용
        if PYZBAR_AVAILABLE:
            try:
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                decoded = pyzbar.decode(gray)
                if decoded:
                    return decoded[0].data.decode('utf-8')
            except Exception as e:
                Logger.warning(f"pyzbar decode error: {e}")
        
        # OpenCV QRCodeDetector 사용
        if OPENCV_QR_AVAILABLE:
            try:
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                retval, decoded_info, points, straight_qrcode = qr_detector.detectAndDecodeMulti(gray)
                if retval and decoded_info:
                    return decoded_info[0]
            except Exception as e:
                Logger.warning(f"OpenCV QR decode error: {e}")
        
        return None
    
    def on_stop(self):
        """앱 종료 시"""
        if self.camera_widget:
            self.camera_widget.play = False


if __name__ == '__main__':
    QRScannerApp().run()
