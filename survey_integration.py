# survey_integration.py
# Googleスプレッドシート連携アンケートシステム（REI版）

import os
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

class SurveyManager:
    """アンケート管理クラス (Googleスプレッドシート連携)"""
    
    def __init__(self, credentials_path='credentials.json', spreadsheet_id=None):
        """
        初期化
        
        Args:
            credentials_path: サービスアカウントのJSONファイルパス
            spreadsheet_id: スプレッドシートのID
        """
        self.credentials_path = credentials_path
        self.spreadsheet_id = spreadsheet_id or os.getenv('SPREADSHEET_ID')
        self.service = None
        self.enabled = False
        
        # 初期化を試行
        self._initialize()
    
    def _initialize(self):
        """Google Sheets APIサービスを初期化"""
        try:
            # 認証情報ファイルの存在確認
            if not os.path.exists(self.credentials_path):
                print(f"⚠️ 認証情報ファイルが見つかりません: {self.credentials_path}")
                print("💡 アンケート機能は無効化されます")
                return
            
            # スプレッドシートIDの確認
            if not self.spreadsheet_id:
                print("⚠️ SPREADSHEET_IDが設定されていません")
                print("💡 アンケート機能は無効化されます")
                return
            
            # 認証情報を読み込み
            SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
            creds = Credentials.from_service_account_file(
                self.credentials_path, 
                scopes=SCOPES
            )
            
            # APIサービスを構築
            self.service = build('sheets', 'v4', credentials=creds)
            self.enabled = True
            
            print(f"✅ Google Sheets API初期化成功")
            print(f"📊 スプレッドシートID: {self.spreadsheet_id[:20]}...")
            
        except Exception as e:
            print(f"❌ Google Sheets API初期化エラー: {e}")
            print("💡 アンケート機能は無効化されます")
            self.enabled = False
    
    def save_survey(self, survey_data):
        """
        アンケート結果をスプレッドシートに保存
        
        Args:
            survey_data: アンケートデータの辞書
                {
                    'avatar_name': アバター名 (例: 'REI'),
                    'visitor_id': 訪問者ID,
                    'quiz_score': クイズスコア (0-3),
                    'conversation_count': 会話回数,
                    'q1': Q1回答,
                    'q2': Q2回答,
                    'q3': Q3回答,
                    'language': 言語 ('ja' or 'en')
                }
        
        Returns:
            bool: 保存成功ならTrue、失敗ならFalse
        """
        if not self.enabled:
            print("⚠️ アンケート機能が無効です")
            return False
        
        try:
            # タイムスタンプを生成
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # スプレッドシートに追加する行データ
            values = [[
                timestamp,
                survey_data.get('avatar_name', 'REI'),
                survey_data.get('visitor_id', 'unknown'),
                survey_data.get('quiz_score', 0),
                survey_data.get('conversation_count', 0),
                survey_data.get('q1', ''),
                survey_data.get('q2', ''),
                survey_data.get('q3', ''),
                survey_data.get('language', 'ja')
            ]]
            
            body = {'values': values}
            
            # スプレッドシートに追加
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range='シート1!A:I',  # A列からI列まで（9列）
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            print(f"✅ アンケート保存成功: {result.get('updates').get('updatedRows')}行追加")
            print(f"🎭 アバター: {survey_data.get('avatar_name')}")
            print(f"📝 データ: Q1={survey_data.get('q1')}, Q2={survey_data.get('q2')}, Q3={survey_data.get('q3')}")
            return True
            
        except HttpError as e:
            print(f"❌ Google Sheets APIエラー: {e}")
            return False
        except Exception as e:
            print(f"❌ アンケート保存エラー: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_survey_stats(self):
        """
        アンケート統計を取得
        
        Returns:
            dict: 統計情報
        """
        if not self.enabled:
            return {'enabled': False}
        
        try:
            # スプレッドシートからデータを取得
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range='シート1!A:I'
            ).execute()
            
            values = result.get('values', [])
            
            if len(values) <= 1:  # ヘッダーのみ
                return {
                    'enabled': True,
                    'total_responses': 0,
                    'average_interest': 0
                }
            
            # 統計計算 (ヘッダー行を除く)
            data_rows = values[1:]
            total = len(data_rows)
            
            # Q2（関心度）の平均を計算
            interest_scores = [int(row[6]) for row in data_rows if len(row) > 6 and row[6].isdigit()]
            avg_interest = sum(interest_scores) / len(interest_scores) if interest_scores else 0
            
            return {
                'enabled': True,
                'total_responses': total,
                'average_interest': round(avg_interest, 2)
            }
            
        except Exception as e:
            print(f"❌ 統計取得エラー: {e}")
            return {'enabled': True, 'error': str(e)}


# ====== アンケート質問定義（REI版 - 京友禅・糸目のり職人） ======
SURVEY_QUESTIONS = {
    'ja': [
        {
            'id': 'q1',
            'type': 'rating',
            'question': '京友禅への関心度や理解度は変化しましたか？',
            'options': [
                {'value': '5', 'label': '5 - 大きく向上した'},
                {'value': '4', 'label': '4 - やや向上した'},
                {'value': '3', 'label': '3 - 変わらない'},
                {'value': '2', 'label': '2 - やや低下した'},
                {'value': '1', 'label': '1 - 低下した'}
            ]
        },
        {
            'id': 'q2',
            'type': 'rating',
            'question': '京友禅の体験工房や商品購入等の意欲は変わりましたか？',
            'options': [
                {'value': '5', 'label': '5 - 大きく高まった'},
                {'value': '4', 'label': '4 - やや高まった'},
                {'value': '3', 'label': '3 - 変わらない'},
                {'value': '2', 'label': '2 - やや低下した'},
                {'value': '1', 'label': '1 - 低下した'}
            ]
        },
        {
            'id': 'q3',
            'type': 'rating',
            'question': 'このアバターとの対話体験を他の方にもすすめたいと思いましたか？',
            'options': [
                {'value': '5', 'label': '5 - 強くそう思う'},
                {'value': '4', 'label': '4 - ややそう思う'},
                {'value': '3', 'label': '3 - どちらともいえない'},
                {'value': '2', 'label': '2 - あまり思わない'},
                {'value': '1', 'label': '1 - 全く思わない'}
            ]
        }
    ],
    'en': [
        {
            'id': 'q1',
            'type': 'rating',
            'question': 'Has your interest in and understanding of Kyo-Yuzen changed?',
            'options': [
                {'value': '5', 'label': '5 - Significantly increased'},
                {'value': '4', 'label': '4 - Somewhat increased'},
                {'value': '3', 'label': '3 - No change'},
                {'value': '2', 'label': '2 - Slightly decreased'},
                {'value': '1', 'label': '1 - Decreased'}
            ]
        },
        {
            'id': 'q2',
            'type': 'rating',
            'question': 'Has your interest in experiencing Kyo-Yuzen workshops or purchasing products changed?',
            'options': [
                {'value': '5', 'label': '5 - Significantly increased'},
                {'value': '4', 'label': '4 - Somewhat increased'},
                {'value': '3', 'label': '3 - No change'},
                {'value': '2', 'label': '2 - Slightly decreased'},
                {'value': '1', 'label': '1 - Decreased'}
            ]
        },
        {
            'id': 'q3',
            'type': 'rating',
            'question': 'Would you recommend this avatar conversation experience to others?',
            'options': [
                {'value': '5', 'label': '5 - Strongly agree'},
                {'value': '4', 'label': '4 - Somewhat agree'},
                {'value': '3', 'label': '3 - Neutral'},
                {'value': '2', 'label': '2 - Somewhat disagree'},
                {'value': '1', 'label': '1 - Strongly disagree'}
            ]
        }
    ]
}

