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
    from pyzbar.pyzbar import decode as pyzbar_decode
    PYZBAR_AVAILABLE = True
    pyzbar = type('obj', (object,), {'decode': pyzbar_decode})
except ImportError:
    try:
        from pyzbar import pyzbar
        PYZBAR_AVAILABLE = True
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
        
        # 하드웨어 성능 극대화 옵션
        self.torch_enabled = False  # 토치(플래시)
        self.zoom_level = 1.0  # 줌 레벨 (1.0 = 기본)
        self.focus_mode = 'continuous_video'  # 연속 오토포커스
        self.macro_mode = False  # 매크로 모드
        self.exposure_compensation = 0  # 노출 보정 (하드웨어)
        
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
        
        # UI 구성 - FloatLayout으로 전체 화면 카메라 + 오버레이 컨트롤
        from kivy.uix.floatlayout import FloatLayout
        layout = FloatLayout()
        
        # 카메라 뷰 (전체 화면)
        if CAMERA4KIVY_AVAILABLE:
            self.camera_widget = Preview(
                camera_id=str(self.camera_index),
                analyze_pixels_resolution=640,  # 분석 해상도 (성능 최적화)
                enable_analyze_pixels=True,
                enable_video=False  # 비디오 녹화 안 함 (성능 확보)
            )
            # 분석 콜백 연결 (Camera4Kivy 방식)
            self.camera_widget.analyze_pixels_resolution_percent = 100
            # analyze_fun은 on_start에서 연결
        else:
            # PC 테스트용 기본 카메라 (기능 제한됨)
            self.camera_widget = Camera(
                index=self.camera_index,
                resolution=(640, 480),
                play=True
            )
            self.camera_widget.bind(on_texture=self.on_camera_frame)
        
        # 카메라를 전체 화면으로
        self.camera_widget.size_hint = (1, 1)
        self.camera_widget.pos_hint = {'x': 0, 'y': 0}
        layout.add_widget(self.camera_widget)
        
        # 상단 오버레이: ROI 표시 및 결과
        top_overlay = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=120,
            pos_hint={'x': 0, 'top': 1},
            padding=10,
            spacing=5
        )
        
        # ROI 표시용 레이블 (반투명 배경)
        from kivy.graphics import Color, Rectangle
        with top_overlay.canvas.before:
            Color(0, 0, 0, 0.5)  # 반투명 검은색
            self.roi_bg = Rectangle(pos=top_overlay.pos, size=top_overlay.size)
        
        self.roi_label = Label(
            text='ROI: (0.2, 0.2) 0.6x0.6',
            size_hint=(1, None),
            height=30,
            color=(1, 1, 1, 1),
            text_size=(None, None),
            halign='center'
        )
        top_overlay.add_widget(self.roi_label)
        
        # 결과 표시
        self.result_label = Label(
            text='QR 코드를 스캔하세요',
            size_hint=(1, None),
            height=60,
            color=(1, 1, 1, 1),
            text_size=(None, None),
            halign='center',
            valign='middle'
        )
        top_overlay.add_widget(self.result_label)
        
        # 상단 오버레이 바인딩 (크기 변경 시 배경 업데이트)
        def update_roi_bg(instance, value):
            self.roi_bg.pos = instance.pos
            self.roi_bg.size = instance.size
        top_overlay.bind(pos=update_roi_bg, size=update_roi_bg)
        
        layout.add_widget(top_overlay)
        
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
        
        # 🎯 포커스 모드
        focus_label = Label(text='포커스 모드', size_hint_y=None, height=30)
        controls.add_widget(focus_label)
        
        focus_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        self.focus_btn = ToggleButton(
            text='연속 포커스',
            size_hint_x=0.5,
            state='down'
        )
        self.focus_btn.bind(on_press=self.toggle_focus_mode)
        focus_layout.add_widget(self.focus_btn)
        
        self.macro_btn = ToggleButton(
            text='매크로 모드',
            size_hint_x=0.5
        )
        self.macro_btn.bind(on_press=self.toggle_macro)
        focus_layout.add_widget(self.macro_btn)
        controls.add_widget(focus_layout)
        
        # 🔍 하드웨어 줌
        zoom_label = Label(text='🔍 하드웨어 줌', size_hint_y=None, height=30)
        controls.add_widget(zoom_label)
        
        zoom_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        zoom_layout.add_widget(Label(text='줌:', size_hint_x=0.2))
        self.zoom_slider = Slider(min=1.0, max=10.0, value=1.0, size_hint_x=0.6)
        self.zoom_slider.bind(value=self.update_zoom)
        zoom_layout.add_widget(self.zoom_slider)
        self.zoom_label = Label(text='1.0x', size_hint_x=0.2)
        zoom_layout.add_widget(self.zoom_label)
        controls.add_widget(zoom_layout)
        
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
        
        # 카메라 설정 (하드웨어 노출 제어)
        camera_settings_label = Label(text='하드웨어 노출 제어', size_hint_y=None, height=30)
        controls.add_widget(camera_settings_label)
        
        # 노출 보정 (하드웨어)
        exposure_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        exposure_layout.add_widget(Label(text='노출:', size_hint_x=0.2))
        self.exposure_slider = Slider(min=-2, max=2, value=0, size_hint_x=0.6)
        self.exposure_slider.bind(value=self.update_exposure_hw)
        exposure_layout.add_widget(self.exposure_slider)
        controls.add_widget(exposure_layout)
        
        # 소프트웨어 후처리 (선택적)
        postprocess_label = Label(text='소프트웨어 후처리', size_hint_y=None, height=30)
        controls.add_widget(postprocess_label)
        
        # 밝기 조정 (소프트웨어)
        brightness_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        brightness_layout.add_widget(Label(text='밝기:', size_hint_x=0.2))
        self.brightness_slider = Slider(min=-1, max=1, value=0, size_hint_x=0.6)
        brightness_layout.add_widget(self.brightness_slider)
        controls.add_widget(brightness_layout)
        
        # 대비 조정 (소프트웨어)
        contrast_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        contrast_layout.add_widget(Label(text='대비:', size_hint_x=0.2))
        self.contrast_slider = Slider(min=0.5, max=2.0, value=1.0, size_hint_x=0.6)
        contrast_layout.add_widget(self.contrast_slider)
        controls.add_widget(contrast_layout)
        
        controls_scroll.add_widget(controls)
        self.controls_panel.add_widget(controls_scroll)
        layout.add_widget(self.controls_panel)
        
        # 설정 버튼 (하단 중앙, 컨트롤 패널 토글)
        self.settings_btn = Button(
            text='⚙️',
            size_hint=(None, None),
            size=(60, 60),
            pos_hint={'center_x': 0.5, 'y': 0.02}
        )
        self.settings_btn.bind(on_press=self.toggle_controls)
        layout.add_widget(self.settings_btn)
        
        return layout
    
    def toggle_controls(self, instance):
        """컨트롤 패널 표시/숨김 토글"""
        self.controls_visible = not self.controls_visible
        
        if self.controls_visible:
            # 컨트롤 패널 표시 (애니메이션)
            from kivy.animation import Animation
            anim = Animation(height=400, duration=0.3)
            anim.start(self.controls_panel)
            instance.text = '✕'
        else:
            # 컨트롤 패널 숨김
            from kivy.animation import Animation
            anim = Animation(height=0, duration=0.3)
            anim.start(self.controls_panel)
            instance.text = '⚙️'
    
    def on_start(self):
        """앱 시작 시 권한 요청 및 카메라 연결"""
        from kivy.utils import platform
        
        # Android 권한 요청
        if platform == 'android':
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.CAMERA,
                    Permission.WRITE_EXTERNAL_STORAGE,
                ])
                Logger.info("Android permissions requested")
            except Exception as e:
                Logger.warning(f"Permission request failed: {e}")
        
        # Camera4Kivy 카메라 연결 및 분석 콜백 설정
        if CAMERA4KIVY_AVAILABLE:
            try:
                # analyze_fun 콜백 연결
                self.camera_widget.analyze_pixels_callback = self.analyze_frame_wrapper
                # 카메라 연결
                self.camera_widget.connect_camera(enable_video=False)
                Logger.info("Camera4Kivy connected")
            except Exception as e:
                Logger.error(f"Camera4Kivy connection failed: {e}")
    
    def analyze_frame_wrapper(self, image_proxy):
        """Camera4Kivy 분석 콜백 - ImageProxy를 받아서 처리"""
        if not self.scanning:
            return
        
        try:
            # ImageProxy를 OpenCV 이미지로 변환
            frame = self.image_proxy_to_opencv(image_proxy)
            if frame is None:
                return
            
            # ROI 영역 추출 (하드웨어 최적화: 가운데 영역만 분석)
            h, w = frame.shape[:2]
            roi_x1 = int(self.roi_x * w)
            roi_y1 = int(self.roi_y * h)
            roi_x2 = int((self.roi_x + self.roi_width) * w)
            roi_y2 = int((self.roi_y + self.roi_height) * h)
            
            roi = frame[roi_y1:roi_y2, roi_x1:roi_x2]
            
            if roi.size == 0:
                return
            
            # 소프트웨어 후처리
            roi = self._apply_postprocessing(roi)
            
            # QR 코드 해독
            decoded_text = self.decode_qr(roi)
            
            if decoded_text and decoded_text != self.last_decoded:
                self.last_decoded = decoded_text
                self.result_label.text = f'✅ 해독 성공:\n{decoded_text[:50]}'
                Logger.info(f"QR decoded: {decoded_text}")
        
        except Exception as e:
            Logger.error(f"Frame analysis error: {e}")
    
    def image_proxy_to_opencv(self, image_proxy):
        """ImageProxy를 OpenCV numpy 배열로 변환"""
        try:
            # Camera4Kivy의 ImageProxy 처리
            # ImageProxy는 Android의 ImageProxy 객체
            if hasattr(image_proxy, 'get_planes'):
                # YUV 포맷 처리
                planes = image_proxy.get_planes()
                if len(planes) > 0:
                    # Y 채널 가져오기
                    y_plane = planes[0]
                    y_buffer = y_plane.get_buffer()
                    y_bytes = bytearray(y_buffer.remaining())
                    y_buffer.get(y_bytes)
                    
                    # 해상도 가져오기
                    width = image_proxy.get_width()
                    height = image_proxy.get_height()
                    
                    # Y 채널을 numpy 배열로 변환
                    y_array = np.frombuffer(y_bytes, dtype=np.uint8)
                    y_array = y_array.reshape((height, width))
                    
                    # 그레이스케일을 BGR로 변환 (QR 인식용)
                    frame = cv2.cvtColor(y_array, cv2.COLOR_GRAY2BGR)
                    return frame
            
            # 대안: RGB 포맷 처리
            if hasattr(image_proxy, 'get_format'):
                # 직접 픽셀 데이터 접근 시도
                try:
                    from jnius import autoclass
                    ByteBuffer = autoclass('java.nio.ByteBuffer')
                    ImageFormat = autoclass('android.graphics.ImageFormat')
                    
                    # ImageProxy에서 직접 픽셀 데이터 가져오기
                    # (구현은 Camera4Kivy 문서 참조)
                    pass
                except:
                    pass
            
            Logger.warning("Could not convert ImageProxy to OpenCV")
            return None
            
        except Exception as e:
            Logger.error(f"ImageProxy conversion error: {e}")
            return None
    
    def toggle_camera(self, instance):
        """카메라 전환 (후면/앞면)"""
        self.camera_index = 1 - self.camera_index
        if CAMERA4KIVY_AVAILABLE:
            try:
                self.camera_widget.disconnect_camera()
                self.camera_widget.camera_id = str(self.camera_index)
                self.camera_widget.connect_camera(enable_video=False)
            except Exception as e:
                Logger.error(f"Camera switch failed: {e}")
        else:
            self.camera_widget.index = self.camera_index
        instance.text = '앞면 카메라' if self.camera_index == 1 else '후면 카메라'
        Logger.info(f"Camera switched to index {self.camera_index}")
    
    def toggle_torch(self, instance):
        """토치(플래시) 토글"""
        self.torch_enabled = not self.torch_enabled
        if CAMERA4KIVY_AVAILABLE:
            try:
                # Camera4Kivy의 토치 제어
                if hasattr(self.camera_widget, 'enable_torch'):
                    self.camera_widget.enable_torch(self.torch_enabled)
                elif hasattr(self.camera_widget, 'torch'):
                    self.camera_widget.torch = self.torch_enabled
                instance.text = '🔦 토치 ON' if self.torch_enabled else '🔦 토치 OFF'
                Logger.info(f"Torch: {self.torch_enabled}")
            except Exception as e:
                Logger.warning(f"Torch control failed: {e}")
                instance.text = '🔦 토치 (오류)'
        else:
            instance.text = '🔦 토치 OFF (미지원)'
    
    def toggle_focus_mode(self, instance):
        """포커스 모드 토글"""
        if instance.state == 'down':
            self.focus_mode = 'continuous_video'
            self.macro_mode = False
            self.macro_btn.state = 'normal'
            Logger.info("Focus mode: continuous_video")
        else:
            self.focus_mode = 'auto'
            Logger.info("Focus mode: auto")
        
        if CAMERA4KIVY_AVAILABLE:
            try:
                # Camera4Kivy의 포커스 모드 설정
                if hasattr(self.camera_widget, 'set_focus_mode'):
                    self.camera_widget.set_focus_mode(self.focus_mode)
            except Exception as e:
                Logger.warning(f"Focus mode setting failed: {e}")
    
    def toggle_macro(self, instance):
        """매크로 모드 토글"""
        self.macro_mode = (instance.state == 'down')
        if self.macro_mode:
            self.focus_mode = 'macro'
            self.focus_btn.state = 'normal'
            Logger.info("Focus mode: macro")
        else:
            self.focus_mode = 'continuous_video'
            self.focus_btn.state = 'down'
        
        if CAMERA4KIVY_AVAILABLE:
            try:
                if hasattr(self.camera_widget, 'set_focus_mode'):
                    self.camera_widget.set_focus_mode(self.focus_mode)
            except Exception as e:
                Logger.warning(f"Macro mode setting failed: {e}")
    
    def update_zoom(self, instance, value):
        """하드웨어 줌 업데이트"""
        self.zoom_level = value
        self.zoom_label.text = f'{value:.1f}x'
        
        if CAMERA4KIVY_AVAILABLE:
            try:
                if hasattr(self.camera_widget, 'set_zoom'):
                    self.camera_widget.set_zoom(value)
                elif hasattr(self.camera_widget, 'zoom'):
                    self.camera_widget.zoom = value
                Logger.info(f"Zoom: {value}x")
            except Exception as e:
                Logger.warning(f"Zoom setting failed: {e}")
    
    def update_exposure_hw(self, instance, value):
        """하드웨어 노출 보정"""
        self.exposure_compensation = value
        
        if CAMERA4KIVY_AVAILABLE:
            try:
                if hasattr(self.camera_widget, 'set_exposure_compensation'):
                    self.camera_widget.set_exposure_compensation(int(value * 10))  # -20 to +20
                Logger.info(f"Exposure compensation: {value}")
            except Exception as e:
                Logger.warning(f"Exposure setting failed: {e}")
    
    def toggle_scan(self, instance):
        """스캔 시작/정지"""
        self.scanning = not self.scanning
        instance.text = '⏸️ 정지' if self.scanning else '▶️ 스캔'
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
            
            # 소프트웨어 후처리
            roi = self._apply_postprocessing(roi)
            
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
    
    def _apply_postprocessing(self, roi):
        """소프트웨어 후처리 적용"""
        # 밝기 조정
        brightness = self.brightness_slider.value
        if brightness != 0:
            roi = cv2.convertScaleAbs(roi, alpha=1, beta=brightness * 50)
        
        # 대비 조정
        contrast = self.contrast_slider.value
        if contrast != 1.0:
            roi = cv2.convertScaleAbs(roi, alpha=contrast, beta=0)
        
        return roi
    
    def on_stop(self):
        """앱 종료 시"""
        if CAMERA4KIVY_AVAILABLE:
            if self.camera_widget:
                try:
                    self.camera_widget.disconnect_camera()
                    Logger.info("Camera4Kivy disconnected")
                except Exception as e:
                    Logger.warning(f"Camera disconnect error: {e}")
        else:
            if self.camera_widget:
                self.camera_widget.play = False


if __name__ == '__main__':
    QRScannerApp().run()
