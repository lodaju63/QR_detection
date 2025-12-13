"""
안드로이드용 QR 코드 스캐너 (Kivy 기반) - Dynamsoft REST API 버전
- Buildozer 빌드 문제 없음 (순수 Python + HTTP 요청)
- Dynamsoft 클라우드 API 사용
- 후면/앞면 카메라 지원
- ROI (Region of Interest) 설정
- 카메라 하드웨어 옵션 조정
"""

import os
import sys
import base64
import json
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from kivy.logger import Logger
import cv2
import numpy as np

# HTTP 요청용 (안드로이드에서 사용 가능)
try:
    from urllib.request import Request, urlopen
    from urllib.error import URLError
    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False
    Logger.error("urllib not available!")

# OpenCV QRCodeDetector (로컬 fallback)
OPENCV_QR_AVAILABLE = False
qr_detector = None
try:
    qr_detector = cv2.QRCodeDetector()
    OPENCV_QR_AVAILABLE = True
except:
    OPENCV_QR_AVAILABLE = False
    Logger.error("OpenCV QRCodeDetector not available!")

# Camera4Kivy 확인 (하드웨어 가속 카메라)
CAMERA4KIVY_AVAILABLE = False
try:
    from camera4kivy import Preview
    CAMERA4KIVY_AVAILABLE = True
    Logger.info("Camera4Kivy found - hardware acceleration enabled")
except ImportError:
    from kivy.uix.camera import Camera
    Logger.warning("Camera4Kivy not found. Using default Camera (limited features).")


class QRScannerApp(App):
    """QR 스캐너 메인 앱 (Dynamsoft REST API 버전)"""
    
    def build(self):
        self.camera_widget = None
        self.roi_x = 0.2
        self.roi_y = 0.2
        self.roi_width = 0.6
        self.roi_height = 0.6
        self.camera_index = 0
        self.last_decoded = None
        self.scanning = False
        self.controls_visible = False
        
        # Dynamsoft REST API 설정
        self.dynamsoft_api_key = os.environ.get(
            'DYNAMSOFT_API_KEY',
            'YOUR_API_KEY_HERE'  # 실제 API 키로 교체 필요
        )
        self.dynamsoft_endpoint = 'https://api.dynamsoft.com/barcode-reader/v3/read'
        self.use_rest_api = True  # REST API 사용 여부
        
        # 하드웨어 성능 옵션
        self.torch_enabled = False
        self.zoom_level = 1.0
        self.focus_mode = 'continuous_video'
        self.macro_mode = False
        self.exposure_compensation = 0
        
        # UI 구성
        layout = FloatLayout()
        
        # 카메라 위젯
        if CAMERA4KIVY_AVAILABLE:
            self.camera_widget = Preview(
                analyze_pixels_resolution=640,
                enable_analyze_pixels=True,
                enable_video=False
            )
            # 분석 콜백 연결
            if hasattr(self.camera_widget, 'analyze_pixels_callback'):
                self.camera_widget.analyze_pixels_callback = self.analyze_frame_wrapper
        else:
            self.camera_widget = Camera(
                index=0,
                resolution=(640, 480),
                play=True
            )
            self.camera_widget.bind(on_texture=self.on_camera_texture)
        
        layout.add_widget(self.camera_widget)
        
        # 상단 오버레이 (ROI 정보 및 결과)
        top_overlay = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=120,
            pos_hint={'top': 1}
        )
        top_overlay.canvas.before.add(self._get_background_rect())
        
        self.roi_label = Label(
            text='ROI: (0.2, 0.2) - (0.8, 0.8)',
            size_hint=(1, None),
            height=40,
            color=(1, 1, 1, 1)
        )
        top_overlay.add_widget(self.roi_label)
        
        self.result_label = Label(
            text='QR 코드를 스캔하세요',
            size_hint=(1, None),
            height=40,
            color=(0, 1, 0, 1)
        )
        top_overlay.add_widget(self.result_label)
        
        self.status_label = Label(
            text='로컬 모드 (OpenCV)',
            size_hint=(1, None),
            height=40,
            color=(1, 1, 0, 1)
        )
        top_overlay.add_widget(self.status_label)
        
        layout.add_widget(top_overlay)
        
        # 컨트롤 패널 (하단, 숨김 가능)
        self.controls_panel = BoxLayout(
            orientation='vertical',
            size_hint=(1, None),
            height=400,
            pos_hint={'y': -0.4}  # 초기에는 화면 밖
        )
        self.controls_panel.canvas.before.add(self._get_background_rect())
        
        controls = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # ROI 슬라이더
        controls.add_widget(Label(text='ROI X:', size_hint=(1, None), height=30))
        self.roi_x_slider = Slider(min=0, max=0.8, value=0.2, step=0.1)
        self.roi_x_slider.bind(value=self.on_roi_change)
        controls.add_widget(self.roi_x_slider)
        
        controls.add_widget(Label(text='ROI Y:', size_hint=(1, None), height=30))
        self.roi_y_slider = Slider(min=0, max=0.8, value=0.2, step=0.1)
        self.roi_y_slider.bind(value=self.on_roi_change)
        controls.add_widget(self.roi_y_slider)
        
        controls.add_widget(Label(text='ROI Width:', size_hint=(1, None), height=30))
        self.roi_width_slider = Slider(min=0.2, max=1.0, value=0.6, step=0.1)
        self.roi_width_slider.bind(value=self.on_roi_change)
        controls.add_widget(self.roi_width_slider)
        
        controls.add_widget(Label(text='ROI Height:', size_hint=(1, None), height=30))
        self.roi_height_slider = Slider(min=0.2, max=1.0, value=0.6, step=0.1)
        self.roi_height_slider.bind(value=self.on_roi_change)
        controls.add_widget(self.roi_height_slider)
        
        # 밝기/대비 슬라이더
        controls.add_widget(Label(text='Brightness:', size_hint=(1, None), height=30))
        self.brightness_slider = Slider(min=-1, max=1, value=0, step=0.1)
        controls.add_widget(self.brightness_slider)
        
        controls.add_widget(Label(text='Contrast:', size_hint=(1, None), height=30))
        self.contrast_slider = Slider(min=0.5, max=2.0, value=1.0, step=0.1)
        controls.add_widget(self.contrast_slider)
        
        # 스크롤 뷰
        controls_scroll = ScrollView(size_hint=(1, 1))
        controls_scroll.add_widget(controls)
        self.controls_panel.add_widget(controls_scroll)
        
        layout.add_widget(self.controls_panel)
        
        # 설정 버튼
        self.settings_btn = Button(
            text='⚙️',
            size_hint=(None, None),
            size=(60, 60),
            pos_hint={'center_x': 0.5, 'y': 0.02},
            background_color=(0, 0, 0, 0.5)
        )
        self.settings_btn.bind(on_press=self.toggle_controls)
        layout.add_widget(self.settings_btn)
        
        # 빠른 액션 버튼들
        quick_actions = BoxLayout(
            size_hint=(None, None),
            size=(200, 60),
            pos_hint={'right': 0.95, 'y': 0.02},
            spacing=10
        )
        
        # 카메라 전환 버튼
        self.camera_switch_btn = Button(
            text='📷',
            size_hint=(None, None),
            size=(60, 60)
        )
        self.camera_switch_btn.bind(on_press=self.switch_camera)
        quick_actions.add_widget(self.camera_switch_btn)
        
        # 스캔 토글 버튼
        self.scan_toggle_btn = ToggleButton(
            text='▶',
            size_hint=(None, None),
            size=(60, 60)
        )
        self.scan_toggle_btn.bind(on_press=self.toggle_scanning)
        quick_actions.add_widget(self.scan_toggle_btn)
        
        # 토치 버튼
        self.torch_btn = ToggleButton(
            text='🔦',
            size_hint=(None, None),
            size=(60, 60)
        )
        self.torch_btn.bind(on_press=self.toggle_torch)
        quick_actions.add_widget(self.torch_btn)
        
        layout.add_widget(quick_actions)
        
        # 주기적 프레임 분석
        Clock.schedule_interval(self.analyze_frame, 1.0 / 10)  # 10 FPS
        
        return layout
    
    def _get_background_rect(self):
        """반투명 배경"""
        from kivy.graphics import Color, Rectangle
        color = Color(0, 0, 0, 0.7)
        rect = Rectangle(pos=self.pos, size=self.size)
        return color, rect
    
    def on_start(self):
        """앱 시작 시"""
        from kivy.utils import platform
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.CAMERA,
                Permission.WRITE_EXTERNAL_STORAGE,
                Permission.INTERNET,  # REST API 사용을 위해 필요
                Permission.FLASHLIGHT
            ])
        
        # Camera4Kivy 연결
        if CAMERA4KIVY_AVAILABLE and self.camera_widget:
            try:
                self.camera_widget.connect_camera(enable_video=False)
                Logger.info("Camera4Kivy connected")
            except Exception as e:
                Logger.warning(f"Camera4Kivy connect error: {e}")
    
    def analyze_frame_wrapper(self, image_proxy):
        """Camera4Kivy 분석 콜백 래퍼"""
        try:
            frame = self.image_proxy_to_opencv(image_proxy)
            if frame is not None:
                self.process_frame(frame)
        except Exception as e:
            Logger.warning(f"Frame analysis error: {e}")
    
    def image_proxy_to_opencv(self, image_proxy):
        """ImageProxy를 OpenCV 이미지로 변환"""
        try:
            import numpy as np
            
            # YUV 플레인 가져오기
            y_plane = image_proxy.get_plane(0)
            u_plane = image_proxy.get_plane(1)
            v_plane = image_proxy.get_plane(2)
            
            y_buffer = y_plane.get_buffer()
            u_buffer = u_plane.get_buffer()
            v_buffer = v_plane.get_buffer()
            
            y_data = np.frombuffer(y_buffer, dtype=np.uint8)
            u_data = np.frombuffer(u_buffer, dtype=np.uint8)
            v_data = np.frombuffer(v_buffer, dtype=np.uint8)
            
            # YUV to BGR 변환 (간단한 버전)
            height = image_proxy.get_height()
            width = image_proxy.get_width()
            
            y = y_data.reshape((height, width))
            u = u_data.reshape((height // 2, width // 2))
            v = v_data.reshape((height // 2, width // 2))
            
            # YUV420 to BGR 변환
            import cv2
            yuv = np.zeros((height, width, 3), dtype=np.uint8)
            yuv[:, :, 0] = y
            yuv[::2, ::2, 1] = u
            yuv[::2, ::2, 2] = v
            
            bgr = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_NV21)
            return bgr
        except Exception as e:
            Logger.warning(f"Image conversion error: {e}")
            return None
    
    def on_camera_texture(self, camera):
        """기본 카메라 텍스처 업데이트"""
        if not self.scanning:
            return
        
        try:
            texture = camera.texture
            if texture:
                # Texture를 numpy 배열로 변환
                size = texture.size
                buf = texture.pixels
                frame = np.frombuffer(buf, dtype=np.uint8)
                frame = frame.reshape((size[1], size[0], 4))  # RGBA
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                self.process_frame(frame)
        except Exception as e:
            Logger.warning(f"Camera texture error: {e}")
    
    def analyze_frame(self, dt):
        """주기적 프레임 분석 (fallback)"""
        if not self.scanning or CAMERA4KIVY_AVAILABLE:
            return
        # 기본 카메라는 on_camera_texture에서 처리
    
    def process_frame(self, frame):
        """프레임 처리 및 QR 해독"""
        if not self.scanning or frame is None:
            return
        
        try:
            # ROI 추출
            h, w = frame.shape[:2]
            x1 = int(self.roi_x * w)
            y1 = int(self.roi_y * h)
            x2 = int((self.roi_x + self.roi_width) * w)
            y2 = int((self.roi_y + self.roi_height) * h)
            
            roi = frame[y1:y2, x1:x2]
            
            if roi.size == 0:
                return
            
            # 후처리
            roi = self._apply_postprocessing(roi)
            
            # QR 해독
            decoded_text = self.decode_qr(roi)
            
            if decoded_text and decoded_text != self.last_decoded:
                self.last_decoded = decoded_text
                self.result_label.text = f'QR: {decoded_text[:50]}...'
                Logger.info(f"QR decoded: {decoded_text}")
        except Exception as e:
            Logger.warning(f"Frame processing error: {e}")
    
    def decode_qr(self, roi):
        """QR 코드 해독 (Dynamsoft REST API 또는 OpenCV)"""
        if roi.size == 0:
            return None
        
        # Dynamsoft REST API 사용
        if self.use_rest_api and HTTP_AVAILABLE and self.dynamsoft_api_key != 'YOUR_API_KEY_HERE':
            try:
                # 이미지를 base64로 인코딩
                _, buffer = cv2.imencode('.jpg', roi, [cv2.IMWRITE_JPEG_QUALITY, 85])
                image_base64 = base64.b64encode(buffer).decode('utf-8')
                
                # API 요청
                request_data = {
                    'ImageBytes': image_base64
                }
                
                req = Request(
                    self.dynamsoft_endpoint,
                    data=json.dumps(request_data).encode('utf-8'),
                    headers={
                        'Content-Type': 'application/json',
                        'x-api-key': self.dynamsoft_api_key
                    }
                )
                
                response = urlopen(req, timeout=5)
                result = json.loads(response.read().decode('utf-8'))
                
                # 결과 파싱
                if 'Results' in result and len(result['Results']) > 0:
                    barcode_text = result['Results'][0].get('BarcodeText', '')
                    if barcode_text:
                        self.status_label.text = 'Dynamsoft REST API'
                        return barcode_text
            except URLError as e:
                Logger.warning(f"Dynamsoft REST API error: {e}")
                # 네트워크 오류 시 로컬 모드로 전환
                self.use_rest_api = False
            except Exception as e:
                Logger.warning(f"Dynamsoft REST API error: {e}")
        
        # OpenCV QRCodeDetector 사용 (로컬 fallback)
        if OPENCV_QR_AVAILABLE:
            try:
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
                retval, decoded_info, points, straight_qrcode = qr_detector.detectAndDecodeMulti(gray)
                if retval and decoded_info:
                    self.status_label.text = '로컬 모드 (OpenCV)'
                    return decoded_info[0]
            except Exception as e:
                Logger.warning(f"OpenCV QR decode error: {e}")
        
        return None
    
    def _apply_postprocessing(self, roi):
        """소프트웨어 후처리"""
        brightness = self.brightness_slider.value
        if brightness != 0:
            roi = cv2.convertScaleAbs(roi, alpha=1, beta=brightness * 50)
        
        contrast = self.contrast_slider.value
        if contrast != 1.0:
            roi = cv2.convertScaleAbs(roi, alpha=contrast, beta=0)
        
        return roi
    
    def on_roi_change(self, instance, value):
        """ROI 변경"""
        self.roi_x = self.roi_x_slider.value
        self.roi_y = self.roi_y_slider.value
        self.roi_width = self.roi_width_slider.value
        self.roi_height = self.roi_height_slider.value
        
        self.roi_label.text = f'ROI: ({self.roi_x:.1f}, {self.roi_y:.1f}) - ({self.roi_x + self.roi_width:.1f}, {self.roi_y + self.roi_height:.1f})'
    
    def toggle_controls(self, instance):
        """설정 패널 토글"""
        self.controls_visible = not self.controls_visible
        if self.controls_visible:
            self.controls_panel.pos_hint = {'y': 0}
        else:
            self.controls_panel.pos_hint = {'y': -0.4}
    
    def switch_camera(self, instance):
        """카메라 전환"""
        self.camera_index = 1 - self.camera_index
        if CAMERA4KIVY_AVAILABLE and self.camera_widget:
            try:
                self.camera_widget.disconnect_camera()
                self.camera_widget.connect_camera(enable_video=False)
            except Exception as e:
                Logger.warning(f"Camera switch error: {e}")
        else:
            if self.camera_widget:
                self.camera_widget.index = self.camera_index
    
    def toggle_scanning(self, instance):
        """스캔 토글"""
        self.scanning = instance.state == 'down'
        if self.scanning:
            instance.text = '⏸'
        else:
            instance.text = '▶'
    
    def toggle_torch(self, instance):
        """토치 토글"""
        self.torch_enabled = instance.state == 'down'
        if CAMERA4KIVY_AVAILABLE and self.camera_widget:
            try:
                if hasattr(self.camera_widget, 'enable_torch'):
                    self.camera_widget.enable_torch(self.torch_enabled)
            except Exception as e:
                Logger.warning(f"Torch toggle error: {e}")
    
    def on_stop(self):
        """앱 종료 시"""
        if CAMERA4KIVY_AVAILABLE and self.camera_widget:
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
