import streamlit as st
import cv2
import tempfile
import os
import time
import pandas as pd
import numpy as np
from PIL import Image

# ================= ⚙️ 설정 (클래스 순서 중요!) =================
# 학습할 때 폴더 순서와 똑같아야 합니다.
CLASS_NAMES = ['2025', '2101', '2102', '2103', '2104', '2105']
# ============================================================

# 라이브러리를 함수 안에서 불러와서 앱 실행 속도 향상
def load_deep_learning_libs():
    import torch
    import torch.nn as nn
    from torchvision import transforms, models
    from ultralytics import YOLO
    return torch, nn, transforms, models, YOLO

def main():
    st.set_page_config(page_title="QR AI 최종 분석기", layout="wide")
    
    st.title("🎥 QR 코드 AI 최종 분석 시스템")
    st.markdown(f"**현재 설정된 클래스:** `{CLASS_NAMES}`")
    st.markdown("---")

    # ---------------- [사이드바] 파일 업로드 ----------------
    with st.sidebar:
        st.header("📂 모델 & 파일 업로드")
        st.info("방금 학습한 'final.pth' 파일을 사용하세요!")
        
        uploaded_video = st.file_uploader("1. 영상 파일 (.mp4)", type=['mp4', 'avi', 'mov'])
        uploaded_resnet = st.file_uploader("2. ResNet 모델 (.pth)", type=['pth'])
        uploaded_yolo = st.file_uploader("3. YOLO 모델 (.pt)", type=['pt'])
        
        st.markdown("---")
        st.caption("Developed for QR Project")

    # ---------------- [탭 구성] 기능 분리 ----------------
    tab1, tab2 = st.tabs(["📺 영상 변환 및 분석", "🩺 이미지 정밀 진단 (확률 그래프)"])

    # ========================================================
    # [Tab 1] 영상 분석 (고속 변환 모드)
    # ========================================================
    with tab1:
        st.subheader("🚀 영상 전체 분석 (끊김 없음)")
        st.write("영상을 AI가 분석하여 결과 영상을 새로 만듭니다. (원본 속도 재생 가능)")
        
        skip_frames = st.slider("분석 밀도 (낮을수록 정밀하지만 느림)", 1, 10, 3, help="몇 프레임마다 QR을 찾을지 설정합니다.")
        btn_run_video = st.button("🎬 분석 시작", type="primary")

        if btn_run_video:
            if not uploaded_video or not uploaded_resnet:
                st.error("⚠️ 영상과 ResNet 모델은 필수입니다!")
            else:
                # 1. 라이브러리 로드 및 준비
                status_box = st.empty()
                progress_bar = st.progress(0)
                status_box.info("⏳ AI 엔진 가동 중... 잠시만 기다려주세요.")
                
                torch, nn, transforms, models, YOLO = load_deep_learning_libs()
                device = torch.device("cpu") # 서버 부하 방지를 위해 CPU 사용

                # 2. 임시 파일 생성
                tfile_video = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                tfile_video.write(uploaded_video.read())
                video_path = tfile_video.name
                
                tfile_resnet = tempfile.NamedTemporaryFile(delete=False, suffix='.pth')
                tfile_resnet.write(uploaded_resnet.read())
                
                # 결과 저장 경로
                output_path = tempfile.mktemp(suffix='.mp4')

                # 3. 모델 로드 (가장 중요한 부분!)
                try:
                    # ResNet18 껍데기 생성 (pretrained=False 필수)
                    classifier = models.resnet18(pretrained=False)
                    classifier.fc = nn.Linear(classifier.fc.in_features, len(CLASS_NAMES))
                    
                    # 가중치 주입
                    checkpoint = torch.load(tfile_resnet.name, map_location=device)
                    classifier.load_state_dict(checkpoint)
                    classifier.eval() # 평가 모드
                except Exception as e:
                    st.error(f"❌ ResNet 모델 로드 실패: {e}")
                    st.stop()

                # YOLO 로드
                if uploaded_yolo:
                    tfile_yolo = tempfile.NamedTemporaryFile(delete=False, suffix='.pt')
                    tfile_yolo.write(uploaded_yolo.read())
                    detector = YOLO(tfile_yolo.name)
                else:
                    detector = YOLO('yolov8n.pt')

                # 전처리기
                preprocess = transforms.Compose([
                    transforms.Resize((224, 224)),
                    transforms.ToTensor(),
                    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
                ])

                # 4. 영상 처리 루프
                cap = cv2.VideoCapture(video_path)
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

                # 코덱 설정 (mp4v가 호환성 좋음)
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

                frame_cnt = 0
                detected_objects = [] # 깜빡임 방지용 메모리

                start_time = time.time()
                status_box.info("🚀 영상 변환 중... (완료되면 자동으로 재생됩니다)")

                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret: break
                    
                    frame_cnt += 1
                    
                    # 진행률 업데이트 (너무 자주는 말고 10프레임마다)
                    if frame_cnt % 10 == 0:
                        p = min(frame_cnt / total_frames, 1.0)
                        progress_bar.progress(p)

                    # --- [AI 탐지 파트] ---
                    if frame_cnt % skip_frames == 0:
                        # YOLO (탐지)
                        results = detector(frame, verbose=False)
                        detected_objects = [] # 초기화

                        for result in results:
                            boxes = result.boxes
                            for box in boxes:
                                x1, y1, x2, y2 = map(int, box.xyxy[0])
                                
                                # 좌표 보정
                                x1, y1 = max(0, x1), max(0, y1)
                                x2, y2 = min(width, x2), min(height, y2)

                                if x2 - x1 < 10 or y2 - y1 < 10: continue

                                # 이미지 잘라서 ResNet (분류)
                                face_img = frame[y1:y2, x1:x2]
                                # ★ 핵심: BGR -> RGB 변환 (이거 안하면 색맹됨)
                                pil_img = Image.fromarray(cv2.cvtColor(face_img, cv2.COLOR_BGR2RGB))
                                input_tensor = preprocess(pil_img).unsqueeze(0)

                                with torch.no_grad():
                                    outputs = classifier(input_tensor)
                                    probs = torch.nn.functional.softmax(outputs[0], dim=0)
                                    conf, idx = torch.max(probs, 0)
                                    label = CLASS_NAMES[idx]
                                    score = conf.item() * 100
                                
                                detected_objects.append((x1, y1, x2, y2, label, score))

                    # --- [그리기 파트] ---
                    for (x1, y1, x2, y2, label, score) in detected_objects:
                        # 색상: 확신도 높으면 초록, 낮으면 노랑
                        color = (0, 255, 0) if score > 80 else (0, 255, 255)
                        
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
                        text = f"{label} ({score:.1f}%)"
                        
                        # 텍스트 배경
                        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
                        cv2.rectangle(frame, (x1, y1 - 35), (x1 + tw, y1), color, -1)
                        # 텍스트 (검은 글씨)
                        cv2.putText(frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)

                    out.write(frame)

                # 자원 해제
                cap.release()
                out.release()
                
                # 완료 처리
                progress_bar.progress(1.0)
                duration = time.time() - start_time
                status_box.success(f"🎉 변환 완료! ({duration:.1f}초 소요)")

                # 영상 재생 및 다운로드
                st.video(output_path)
                with open(output_path, "rb") as f:
                    st.download_button("💾 결과 영상 다운로드", f, file_name="qr_result_final.mp4")

                # 청소
                os.remove(video_path)
                os.remove(tfile_resnet.name)
                if uploaded_yolo: os.remove(tfile_yolo.name)

    # ========================================================
    # [Tab 2] 이미지 진단 (확률 그래프)
    # ========================================================
    with tab2:
        st.subheader("🩺 이미지 정밀 진단")
        st.write("이미지를 업로드하면 AI가 생각하는 **확률 분포**를 보여줍니다. (99%가 나오는지 확인하세요!)")
        
        uploaded_images = st.file_uploader("테스트할 이미지들 (여러 장 선택 가능)", type=['jpg', 'png', 'jpeg'], accept_multiple_files=True)
        btn_diagnose = st.button("🔍 진단 시작", type="primary")

        if btn_diagnose:
            if not uploaded_images or not uploaded_resnet:
                st.error("이미지와 ResNet 모델을 올려주세요.")
            else:
                torch, nn, transforms, models, YOLO = load_deep_learning_libs()
                
                # 모델 로드 (Tab 1과 동일 로직)
                tfile_resnet = tempfile.NamedTemporaryFile(delete=False, suffix='.pth')
                tfile_resnet.write(uploaded_resnet.read())
                
                device = torch.device("cpu")
                classifier = models.resnet18(pretrained=False)
                classifier.fc = nn.Linear(classifier.fc.in_features, len(CLASS_NAMES))
                classifier.load_state_dict(torch.load(tfile_resnet.name, map_location=device))
                classifier.eval()

                preprocess = transforms.Compose([
                    transforms.Resize((224, 224)),
                    transforms.ToTensor(),
                    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
                ])

                st.markdown("---")
                
                for img_file in uploaded_images:
                    col_L, col_R = st.columns([1, 2])
                    
                    image = Image.open(img_file).convert('RGB')
                    input_tensor = preprocess(image).unsqueeze(0)

                    with torch.no_grad():
                        outputs = classifier(input_tensor)
                        probs = torch.nn.functional.softmax(outputs[0], dim=0)
                        
                        # 데이터프레임 변환
                        prob_list = probs.numpy() * 100
                        df = pd.DataFrame({
                            'Class': CLASS_NAMES,
                            'Confidence (%)': prob_list
                        })
                        
                        top_score = np.max(prob_list)
                        top_label = CLASS_NAMES[np.argmax(prob_list)]

                    # 왼쪽: 이미지
                    with col_L:
                        st.image(image, caption=img_file.name, use_container_width=True)
                        if top_score > 90:
                            st.success(f"결과: **{top_label}**")
                        elif top_score > 50:
                            st.warning(f"결과: {top_label} (애매함)")
                        else:
                            st.error(f"결과: {top_label} (확신 부족)")

                    # 오른쪽: 그래프
                    with col_R:
                        st.subheader(f"확신도: **{top_score:.2f}%**")
                        st.bar_chart(df.set_index('Class'))
                    
                    st.divider()

                os.remove(tfile_resnet.name)

if __name__ == "__main__":
    main()