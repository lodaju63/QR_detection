import streamlit as st
import torch
import torch.nn as nn
import segmentation_models_pytorch as smp
from torchvision import transforms
from PIL import Image
import numpy as np
import cv2
from pyzbar.pyzbar import decode
import io

# ==========================================
# 1. 모델 로드 (학습하신 Unet-ResNet18 구조)
# ==========================================
def load_model(model_path, device):
    model = smp.Unet(
        encoder_name="resnet18",
        encoder_weights=None,
        in_channels=3,
        classes=3,
        activation='sigmoid'
    )
    checkpoint = torch.load(model_path, map_location=device)
    # state_dict 키 정리 (module. 제거 등)
    if isinstance(checkpoint, dict) and 'state_dict' in checkpoint:
        state_dict = checkpoint['state_dict']
    else:
        state_dict = checkpoint
    
    new_state_dict = {k.replace("module.", ""): v for k, v in state_dict.items()}
    model.load_state_dict(new_state_dict)
    model.to(device)
    model.eval()
    return model

# ==========================================
# 2. QR 해독 함수
# ==========================================
def decode_qr(image_np):
    """이미지에서 QR코드를 찾아 해독한 결과를 반환"""
    # pyzbar는 BGR 또는 Gray 스케일에서 잘 작동하므로 변환
    gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    decoded_objects = decode(gray)
    
    results = []
    for obj in decoded_objects:
        results.append({
            'data': obj.data.decode('utf-8'),
            'type': obj.type,
            'rect': obj.rect
        })
    return results

# ==========================================
# 3. 메인 앱 레이아웃
# ==========================================
def main():
    st.set_page_config(page_title="QR 복원 & 해독기", layout="wide")
    st.title("🛡️ QR 코드 복원 및 해독 시스템")
    st.markdown("훼손된 QR 이미지를 **U-Net**으로 복원한 후 내용을 읽어옵니다.")

    with st.sidebar:
        st.header("⚙️ 설정")
        model_file = st.file_uploader("복원 모델 (.pth) 업로드", type=["pth", "pt"])
        # 이미지 출력 크기를 조절할 수 있는 슬라이더 추가
        display_width = st.slider("화면 표시 이미지 크기", 200, 800, 400)
        input_size = st.number_input("입력 크기 (Resize)", value=256, step=32)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        st.info(f"사용 장치: {device}")

    uploaded_files = st.file_uploader("이미지 업로드 (여러 장 가능)", 
                                    type=["jpg", "png", "jpeg"], 
                                    accept_multiple_files=True)

    if model_file and uploaded_files:
        if st.button("🚀 분석 시작", type="primary"):
            try:
                model = load_model(model_file, device)
                transform = transforms.Compose([
                    transforms.Resize((input_size, input_size)),
                    transforms.ToTensor(),
                ])

                for uploaded_file in uploaded_files:
                    st.divider()
                    st.subheader(f"📄 {uploaded_file.name}")
                    
                    # 이미지 로드 및 복원 과정 (기존과 동일)
                    img = Image.open(uploaded_file).convert('RGB')
                    orig_w, orig_h = img.size
                    input_tensor = transform(img).unsqueeze(0).to(device)
                    
                    with torch.no_grad():
                        output = model(input_tensor)
                        restored_np = output.squeeze().cpu().permute(1, 2, 0).numpy()
                        restored_np = (restored_np * 255).astype(np.uint8)
                    
                    restored_final = cv2.resize(restored_np, (orig_w, orig_h), interpolation=cv2.INTER_LANCZOS4)

                    # 해독 시도
                    decoded_orig = decode_qr(np.array(img))
                    decoded_restored = decode_qr(restored_final)

                    # --- 화면 출력 레이아웃 수정 ---
                    # 양옆에 빈 공간을 두어 중앙으로 모으고 크기를 조절함
                    empty_l, col1, col2, empty_r = st.columns([0.5, 1, 1, 0.5])
                    
                    with col1:
                        # use_container_width=True 대신 사용자가 설정한 width 적용
                        st.image(img, caption="훼손된 원본", width=display_width)
                        if decoded_orig:
                            st.success(f"✅ 원본 성공: {decoded_orig[0]['data']}")
                        else:
                            st.error("❌ 원본 해독 실패")

                    with col2:
                        st.image(restored_final, caption="U-Net 복원 결과", width=display_width)
                        if decoded_restored:
                            st.success(f"🎉 복원 성공: {decoded_restored[0]['data']}")
                        else:
                            st.error("❌ 복원 해독 실패")

            except Exception as e:
                st.error(f"오류 발생: {e}")

if __name__ == "__main__":
    main()