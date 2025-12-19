import os
from PIL import Image
from torchvision import transforms
from tqdm import tqdm
import torch

# ==============================================================================
# [설정] Unknown 폴더만 따로 증강하기
# ==============================================================================

# 1. 원본 18장이 들어있는 폴더 경로 (선생님이 만드신 경로)
# 예: C:\Users\Administrator\QR_project\unknown
INPUT_SPECIFIC_DIR = r"C:\Users\Administrator\QR_project\unknown"

# 2. 증강된 파일이 저장될 최종 경로 (기존 train_augmented_jpg 안에 9999_unknown으로 저장)
# 이렇게 해야 나중에 압축할 때 합치기 편합니다.
OUTPUT_FINAL_DIR = r"C:\Users\Administrator\QR_project\train_augmented_jpg\9999_unknown"

# 3. 증강 배수 (18장 * 50배 = 900장)
AUGMENT_TIMES = 50 

# ==============================================================================
# 증강 파이프라인 (기존과 동일하게 강력한 가림 효과 포함)
# ==============================================================================
augment_transform = transforms.Compose([
    transforms.RandomPerspective(distortion_scale=0.5, p=0.5),
    transforms.RandomRotation(degrees=20),
    transforms.ColorJitter(brightness=0.4, contrast=0.4, saturation=0.2),
    transforms.GaussianBlur(kernel_size=3, sigma=(0.1, 2.0)),
    transforms.RandomResizedCrop(224, scale=(0.7, 1.0), ratio=(0.9, 1.1)),
    
    # 가림 효과 (Random Erasing)
    transforms.ToTensor(),
    transforms.RandomErasing(p=0.6, scale=(0.02, 0.20), ratio=(0.3, 3.3), value='random'),
    transforms.ToPILImage()
])

resize_transform = transforms.Resize((224, 224))

def augment_specific_folder():
    # 폴더 확인
    if not os.path.exists(INPUT_SPECIFIC_DIR):
        print(f"❌ 입력 폴더를 찾을 수 없습니다: {INPUT_SPECIFIC_DIR}")
        print("경로를 다시 확인해주세요.")
        return

    # 출력 폴더 생성
    os.makedirs(OUTPUT_FINAL_DIR, exist_ok=True)
    
    # 이미지 파일 찾기
    images = [f for f in os.listdir(INPUT_SPECIFIC_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    print(f"🚀 Unknown 데이터 증강 시작! (원본 {len(images)}장 -> 목표 {len(images)*AUGMENT_TIMES}장)")
    print(f"📂 저장 위치: {OUTPUT_FINAL_DIR}")

    count = 0
    for img_file in tqdm(images, desc="Unknown Processing"):
        try:
            # 이미지 로드
            src_path = os.path.join(INPUT_SPECIFIC_DIR, img_file)
            src = Image.open(src_path).convert('RGB')
            base_name = os.path.splitext(img_file)[0]
            
            # 1. 원본 저장
            resize_transform(src).save(os.path.join(OUTPUT_FINAL_DIR, f"unknown_{base_name}_orig.jpg"), quality=95)
            
            # 2. 증강 저장
            for i in range(AUGMENT_TIMES):
                aug_img = augment_transform(src)
                save_name = f"unknown_{base_name}_aug_{i}.jpg"
                aug_img.save(os.path.join(OUTPUT_FINAL_DIR, save_name), quality=90)
                count += 1
                
        except Exception as e:
            print(f"⚠️ 오류 발생 ({img_file}): {e}")

    print("\n" + "="*50)
    print(f"✅ 완료! 총 {count}장의 Unknown 데이터가 생성되었습니다.")
    print(f"이제 'train_augmented_jpg' 폴더 안에 총 5개의 폴더가 있는지 확인하세요.")

if __name__ == "__main__":
    augment_specific_folder()