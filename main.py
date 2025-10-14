import argparse
from data_manager import DataManager
from qr_decoder import QRDecoder
from video_processor import VideoProcessor

def main(video_path, excel_output_path):
    """프로그램의 메인 실행 함수"""
    
    # 모듈 인스턴스화
    data_manager = DataManager()
    qr_decoder = QRDecoder()
    
    try:
        video_processor = VideoProcessor(video_path, qr_decoder, data_manager)
        
        # 영상 처리 실행
        video_processor.process_video()
        
        # 결과 엑셀로 내보내기
        data_manager.export_to_excel(excel_output_path)

    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"예기치 않은 오류 발생: {e}")
    finally:
        # 데이터베이스 연결 종료
        data_manager.close()
        print("프로그램을 종료합니다.")


if __name__ == '__main__':
    # 명령줄 인자 파서 설정
    parser = argparse.ArgumentParser(description="실시간 영상 QR코드 인식 프로그램")
    parser.add_argument("video_file", type=str, help="처리할 영상 파일 경로")
    parser.add_argument("-o", "--output", type=str, default="qr_scan_results.xlsx", help="결과를 저장할 엑셀 파일 이름")
    
    args = parser.parse_args()
    
    # 메인 함수 실행
    main(args.video_file, args.output)