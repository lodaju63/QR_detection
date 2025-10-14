import sqlite3
import pandas as pd
from datetime import datetime
import os # 파일명 추출을 위해 추가

class BatchTestDataManager:
    """
    배치 테스트 결과를 저장하고 엑셀로 내보내는 임시 데이터 관리 클래스.
    기존 DataManager.py를 수정하지 않고 테스트 전용으로 사용됩니다.
    """
    def __init__(self, db_path='batch_test_results.db'):
        """
        데이터베이스 연결 및 테스트 결과 테이블 생성.
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        """
        배치 테스트 결과를 위한 테이블을 생성합니다.
        """
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS BatchTestResults (
                resultId INTEGER PRIMARY KEY AUTOINCREMENT,
                runTimestamp TEXT NOT NULL,          -- 테스트 실행 시각
                imageFileName TEXT NOT NULL,         -- 원본 이미지 파일명
                imageFilePath TEXT NOT NULL,         -- 원본 이미지 파일의 전체 경로
                processedOutputImagePath TEXT NOT NULL, -- 처리 후 저장된 이미지 파일의 전체 경로
                qrCodeData TEXT,                     -- 인식된 QR 데이터 (해독 실패 시 NULL)
                qrCodeLocation TEXT,                 -- QR 코드 위치 (bbox 문자열)
                qrCodeStatus TEXT NOT NULL,          -- 인식 상태 ('SUCCESS', 'FAILED_DECODING', 'NO_QR_DETECTED')
                processingTimePerImage REAL NOT NULL -- 해당 이미지 처리 시간 (초)
            )
        ''')
        self.conn.commit()

    def add_test_result(self, image_file_name, image_file_path, processed_output_image_path,
                        qr_code_data, qr_code_location, qr_code_status, processing_time_per_image):
        """
        단일 이미지 처리 결과를 데이터베이스에 추가합니다.
        하나의 이미지에 여러 QR 코드가 있다면, 각각의 QR 코드에 대해 이 함수가 호출됩니다.
        QR 코드를 찾지 못한 이미지라면 qr_code_data, qr_code_location은 NULL이 될 수 있습니다.
        """
        run_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute(
            "INSERT INTO BatchTestResults (runTimestamp, imageFileName, imageFilePath, processedOutputImagePath, "
            "qrCodeData, qrCodeLocation, qrCodeStatus, processingTimePerImage) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (run_timestamp, image_file_name, image_file_path, processed_output_image_path,
             qr_code_data, qr_code_location, qr_code_status, processing_time_per_image)
        )
        self.conn.commit()

    def export_to_excel(self, file_name='batch_test_results.xlsx'):
        """DB에 저장된 배치 테스트 결과를 엑셀 파일로 저장합니다."""
        query = """
            SELECT
                runTimestamp AS '테스트 실행 시각',
                imageFileName AS '원본 이미지 파일명',
                imageFilePath AS '원본 이미지 경로',
                processedOutputImagePath AS '처리된 이미지 경로',
                qrCodeData AS 'QR 데이터',
                qrCodeLocation AS 'QR 위치 (x,y,w,h)',
                qrCodeStatus AS '인식 상태',
                processingTimePerImage AS '이미지 처리 시간 (초)'
            FROM BatchTestResults
            ORDER BY runTimestamp, imageFileName;
        """
        df = pd.read_sql_query(query, self.conn)
        df.to_excel(file_name, index=False, engine='openpyxl')
        print(f"\n배치 테스트 결과가 '{file_name}' 파일로 저장되었습니다.")

    def close(self):
        """데이터베이스 연결을 종료합니다."""
        self.conn.close()
        print(f"배치 테스트 DB 연결 종료: '{self.db_path}'")

    def reset_database(self):
        """테이블을 삭제하고 다시 생성하여 데이터베이스를 초기화합니다."""
        self.cursor.execute("DROP TABLE IF EXISTS BatchTestResults")
        self.conn.commit()
        self._create_tables() # <--- ✨ 여기가 추가된 부분입니다!
        print(f"배치 테스트 DB '{self.db_path}' 초기화 완료.")