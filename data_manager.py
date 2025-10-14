import sqlite3
import pandas as pd
from datetime import datetime

class DataManager:
    """
    데이터베이스 및 파일 입출력 관리
    """
    def __init__(self, db_path='qr_data.db'):
        """
        데이터베이스 연결 및 테이블 생성
        """
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Video (
                videoId INTEGER PRIMARY KEY AUTOINCREMENT,
                filePath TEXT NOT NULL,
                updateTime TEXT NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Frame (
                frameId INTEGER PRIMARY KEY AUTOINCREMENT,
                videoId INTEGER,
                time REAL NOT NULL,
                imagePath TEXT,
                FOREIGN KEY (videoId) REFERENCES Video(videoId)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS QRCode (
                qrCodeId INTEGER PRIMARY KEY AUTOINCREMENT,
                frameId INTEGER,
                data TEXT,
                time REAL NOT NULL,
                location TEXT,
                status TEXT,
                FOREIGN KEY (frameId) REFERENCES Frame(frameId)
            )
        ''')
        self.conn.commit()

    def add_video(self, file_path):
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute("INSERT INTO Video (filePath, updateTime) VALUES (?, ?)", (file_path, current_time))
        self.conn.commit()
        return self.cursor.lastrowid

    def add_frame(self, video_id, timestamp, image_path=None):
        self.cursor.execute("INSERT INTO Frame (videoId, time, imagePath) VALUES (?, ?, ?)", (video_id, timestamp, image_path))
        self.conn.commit()
        return self.cursor.lastrowid

    def add_qr_code(self, frame_id, qr_result, timestamp):
        data = qr_result.get('data')
        location = str(qr_result.get('location'))
        status = qr_result.get('status')
        
        self.cursor.execute(
            "INSERT INTO QRCode (frameId, data, time, location, status) VALUES (?, ?, ?, ?, ?)",
            (frame_id, data, timestamp, location, status)
        )
        self.conn.commit()

    def export_to_excel(self, file_name='qr_scan_results.xlsx'):
        """DB의 QR코드 정보를 엑셀 파일로 저장"""
        query = """
            SELECT
                v.filePath AS '영상 파일 경로',
                f.time AS '프레임 시간 (초)',
                q.data AS 'QR 데이터',
                q.status AS '인식 상태',
                q.location AS 'QR 위치 (x1, y1, x2, y2)'
            FROM QRCode q
            JOIN Frame f ON q.frameId = f.frameId
            JOIN Video v ON f.videoId = v.videoId
            ORDER BY v.filePath, f.time;
        """
        df = pd.read_sql_query(query, self.conn)
        df.to_excel(file_name, index=False, engine='openpyxl')
        print(f"결과가 '{file_name}' 파일로 저장되었습니다.")

    def close(self):
        """데이터베이스 연결 종료"""
        self.conn.close()