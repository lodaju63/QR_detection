import streamlit as st
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
import numpy as np
import os
import io

# ==============================================================================
# 1. 설정 변수
# ==============================================================================
CLASS_NAMES = ['2025', '2101', '2102', '2103'] 
NUM_CLASSES = len(CLASS_NAMES)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ------------------------------------------------------------------------------
# 2. 모델 로드 함수 (업로드된 파일 기반)
# ------------------------------------------------------------------------------
@st.cache_resource
def load_resnet_model(uploaded_resnet_file, num_classes):
    """업로드된 ResNet 모델 가중치를 로드하고 캐싱합니다."""
    if uploaded_resnet_file is None:
        return None
        
    model = models.resnet18(weights=None)
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, num_classes)
    
    try:
        # 업로드된 파일 객체에서 직접 가중치 로드
        model.load_state_dict(torch.load(uploaded_resnet_file, map_location=device))
        model.eval()
        model.to(device)
        return model
    except Exception as e:
        st.error(f"❌ ResNet 모델 로드 중 오류 발생: {e}")
        return None

@st.cache_resource
def load_yolo_model(uploaded_yolo_file):
    """업로드된 YOLO 모델을 로드합니다. (실제 YOLO 코드로 대체해야 함)"""
    if uploaded_yolo_file is None:
        return None
        
    try:
        # --- 실제 YOLO 모델 로드 코드로 대체하세요 ---
        # 예: yolo_model = YOLO(uploaded_yolo_file.name) # YOLOv8은 파일명을 참조
        #     st.success("✅ YOLO 모델 로드 성공.")
        #     return yolo_model
        
        # 현재는 더미 모델 반환
        st.success("✅ YOLO 모델 로드 (더미) 성공.")
        return True # 로드 성공을 가정
        
    except Exception as e:
        st.error(f"❌ YOLO 모델 로드 중 오류 발생: {e}")
        return None

# ==============================================================================
# 3. 분류 및 시각화 파이프라인 (이전과 동일)
# ==============================================================================

# ResNet 분류 전처리 정의
classification_transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def process_image(full_image, resnet_model, yolo_model, class_names):
    """단일 이미지에 대해 탐지, 분류 및 시각화를 수행합니다."""
    W, H = full_image.size
    
    # --- 2. YOLO 탐지 (임시 더미 박스 사용) ---
    # 실제 YOLO 모델을 사용한다면 이 부분을 YOLO 코드 및 모델 로드로 대체해야 합니다.
    detected_boxes = np.array([[W*0.2, H*0.2, W*0.8, H*0.8]]) 
    # --------------------------------------------------------------------------
    
    if len(detected_boxes) == 0:
        return full_image, None, None, "❌ 탐지 실패: QR 코드를 찾을 수 없습니다."
    
    # 3. 분류 (탐지된 첫 번째 QR 코드만 처리)
    box = detected_boxes[0]
    xmin, ymin, xmax, ymax = map(int, box)
    
    cropped_qr = full_image.crop((xmin, ymin, xmax, ymax))
    
    # ResNet 입력 전처리 및 예측
    input_tensor = classification_transform(cropped_qr)
    input_batch = input_tensor.unsqueeze(0).to(device)
    
    with torch.no_grad():
        output = resnet_model(input_batch)
    
    # 3-3. 결과 해석
    probabilities = torch.nn.functional.softmax(output[0], dim=0)
    top_p, top_class_index = probabilities.topk(1, dim=0)
    
    predicted_class = class_names[top_class_index.item()]
    all_probabilities = probabilities.cpu().numpy()

    return full_image, (xmin, ymin, xmax, ymax), all_probabilities, predicted_class

def draw_and_plot(full_image, box, all_probabilities, predicted_class, class_names):
    """이미지 및 확신도 그래프를 시각화합니다."""
    # Matplotlib 시각화 코드 (이전과 동일)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    if box:
        draw = ImageDraw.Draw(full_image)
        xmin, ymin, xmax, ymax = box
        draw.rectangle([xmin, ymin, xmax, ymax], outline="green", width=4)
        
    ax1.imshow(full_image)
    ax1.set_title(f"탐지 및 분류된 이미지 (예측: {predicted_class})", fontsize=15)
    ax1.axis('off')

    y_pos = np.arange(len(class_names))
    ax2.barh(y_pos, all_probabilities * 100, align='center', color='skyblue')
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels(class_names, fontsize=12)
    ax2.invert_yaxis()
    ax2.set_xlabel('확신도 (%)', fontsize=12)
    ax2.set_title('QR 코드 종류별 분류 확신도', fontsize=15)
    
    for i, p in enumerate(all_probabilities):
        ax2.text(p * 100 + 1, i, f'{p*100:.2f}%', va='center', fontsize=10)

    plt.tight_layout()
    return fig

# ==============================================================================
# 4. Streamlit UI 구성 및 실행
# ==============================================================================
def main():
    st.set_page_config(layout="wide")
    st.title("🚀 QR 코드 YOLO 탐지 및 ResNet 분류 시스템 (모델 업로드)")
    st.markdown("### 1. 모델 파일 업로드 후, 2. 테스트 이미지를 업로드하세요.")

    st.sidebar.header("1. 모델 파일 업로드")
    
    # 1-1. ResNet 모델 업로드
    uploaded_resnet_file = st.sidebar.file_uploader(
        "ResNet 분류 모델 (**.pth** 파일)", 
        type=['pth']
    )
    
    # 1-2. YOLO 모델 업로드
    uploaded_yolo_file = st.sidebar.file_uploader(
        "YOLO 탐지 모델 (**.pt** 파일)", 
        type=['pt']
    )

    # 2. 모델 로드
    resnet_model = load_resnet_model(uploaded_resnet_file, NUM_CLASSES)
    yolo_model = load_yolo_model(uploaded_yolo_file)
    
    if resnet_model is None or yolo_model is None:
        st.warning("⚠️ 분류 모델과 탐지 모델 파일을 모두 업로드해야 시스템이 작동합니다.")
        st.stop()
        
    st.sidebar.markdown("---")
    st.sidebar.header("2. 설정 정보")
    st.sidebar.write(f"**ResNet 클래스:** {NUM_CLASSES}개 ({', '.join(CLASS_NAMES)})")
    st.sidebar.write(f"**사용 디바이스:** {device}")
    st.sidebar.markdown("---")


    # 3. 이미지 업로드 위젯
    uploaded_images = st.file_uploader(
        "분류할 이미지 파일을 선택하세요 (PNG 또는 JPG, 여러 파일 선택 가능)", 
        type=['png', 'jpg', 'jpeg'], 
        accept_multiple_files=True
    )

    if uploaded_images:
        st.subheader(f"총 {len(uploaded_images)}개 파일 처리 결과:")
        
        # 4. 업로드된 파일 반복 처리
        for uploaded_image in uploaded_images:
            st.markdown(f"#### 🖼️ 파일명: `{uploaded_image.name}`")
            
            full_image = Image.open(uploaded_image).convert('RGB')
            
            with st.spinner('탐지 및 분류 중...'):
                result_image, box, all_probs, prediction = process_image(
                    full_image, resnet_model, yolo_model, CLASS_NAMES
                )

            if box:
                st.write(f"**예측 결과:** **{prediction}** (확신도: {all_probs.max() * 100:.2f}%)")
                
                fig = draw_and_plot(result_image, box, all_probs, prediction, CLASS_NAMES)
                st.pyplot(fig)
            else:
                st.error(prediction) 
                
# 앱 실행
if __name__ == '__main__':
    # 폰트 설정 (로컬 Windows 환경 가정)
    try:
        plt.rcParams['font.family'] = 'Malgun Gothic'
        plt.rcParams['axes.unicode_minus'] = False # 마이너스 폰트 깨짐 방지
    except:
        pass # 폰트 설정 실패 시 기본 폰트 사용
        
    main()