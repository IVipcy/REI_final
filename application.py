import os
import time
import json
import uuid
import hashlib
import tempfile
import numpy as np
import re
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional, Set, Any
from flask import Flask, render_template, request, jsonify, make_response, send_file
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from openai import OpenAI
import tiktoken
from pathlib import Path
from scipy.io import wavfile
import base64
import requests
from modules.rag_system import RAGSystem
from modules.speech_processor import SpeechProcessor
from pathlib import Path
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()

# PIL/Pillow for reward image
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("⚠️ Pillow library not installed - quiz reward image will use fallback")
    Image = None

# アンケートシステム (Googleスプレッドシート連携)
try:
    from survey_integration import SurveyManager, SURVEY_QUESTIONS
    survey_manager = SurveyManager()
    print(f"✅ アンケートシステム初期化: enabled={survey_manager.enabled}")
except ImportError as e:
    print(f"⚠️ アンケートシステムのインポートエラー: {e}")
    survey_manager = None
    SURVEY_QUESTIONS = {'ja': [], 'en': []}
except Exception as e:
    print(f"⚠️ アンケートシステム初期化エラー: {e}")
    survey_manager = None
    SURVEY_QUESTIONS = {'ja': [], 'en': []}

# ====== 初期設定 ======
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['SECRET_KEY'] = 'secret!'

# WebSocket設定(シンプル版)
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading'  # Python 3.13対応
)

# ====== 🎯 感情分析システム(改善版) ======
class EmotionAnalyzer:
    def __init__(self):
        # 感情キーワード辞書(優先度順・拡張版)
        self.emotion_keywords = {
            'happy': {
                'keywords': [
                    'うれしい', '嬉しい', 'ウレシイ', 'ureshii',
                    '楽しい', 'たのしい', 'tanoshii',
                    'ハッピー', 'happy', 'はっぴー',
                    '喜び', 'よろこび', 'yorokobi',
                    '幸せ', 'しあわせ', 'shiawase',
                    '最高', 'さいこう', 'saikou',
                    'やった', 'yatta',
                    'わーい', 'わあい', 'waai',
                    '笑', 'わら', 'wara',
                    '良い', 'いい', 'よい', 'yoi',
                    '素晴らしい', 'すばらしい', 'subarashii',
                    'ありがとう', 'ありがと', 'おかげ',
                    '感謝', 'かんしゃ', '感動', 'かんどう',
                    '面白い', 'おもしろい', 'たのしみ',
                    'ワクワク', 'わくわく', 'ドキドキ',
                    # 新規追加
                    'うまい', '美味しい', 'おいしい', '美味',
                    '完璧', 'かんぺき', 'perfect',
                    'グッド', 'good', 'nice', 'ナイス',
                    '愛してる', '大好き', 'だいすき',
                    'すごく良い', 'とても良い', '非常に良い'
                ],
                'patterns': [r'♪+', r'〜+$', r'www', r'笑$'],
                'weight': 1.3
            },
            'sad': {
                'keywords': [
                    '悲しい', 'かなしい', 'カナシイ', 'kanashii',
                    '寂しい', 'さびしい', 'さみしい', 'sabishii',
                    '泣', 'なく', 'naku',
                    '涙', 'なみだ', 'namida',
                    '辛い', 'つらい', 'tsurai',
                    '苦しい', 'くるしい', 'kurushii',
                    '切ない', 'せつない', 'setsunai',
                    'しんどい', 'shindoi',
                    '失望', 'しつぼう', 'shitsubou',
                    '落ち込', 'おちこ', 'ochiko',
                    'がっかり', 'gakkari',
                    '憂鬱', 'ゆううつ', 'yuuutsu',
                    'ブルー', 'blue', 'ぶるー',
                    # 新規追加
                    '残念', 'ざんねん', 'zannen',
                    '悔しい', 'くやしい', 'kuyashii',
                    '孤独', 'こどく', 'kodoku',
                    'ひとりぼっち', 'hitoribocchi',
                    '絶望', 'ぜつぼう', 'zetsubou',
                    'つまらない', 'tsumaranai',
                    '不幸', 'ふこう', 'fukou'
                ],
                'patterns': [r'。。。', r'…+$', r'T[T_]T', r';;', r'泣$'],
                'weight': 1.2
            },
            'angry': {
                'keywords': [
                    '怒', 'おこ', 'oko',
                    'イライラ', 'いらいら', 'iraira',
                    'ムカつく', 'むかつく', 'mukatsuku',
                    'ムカムカ', 'むかむか', 'mukamuka',
                    '腹立', 'はらだ', 'harada',
                    'キレ', 'きれ', 'kire',
                    '憤', 'いきどお', 'ikidoo',
                    'ふざけ', 'fuzake',
                    '最悪', 'さいあく', 'saiaku',
                    'うざい', 'うざ', 'uzai',
                    'やばい', 'yabai',
                    # 新規追加
                    '頭にくる', 'あたまにくる', 'atamanikuru',
                    '許せない', 'ゆるせない', 'yurusenai',
                    '納得いかない', 'なっとくいかない',
                    '不愉快', 'ふゆかい', 'fuyukai',
                    '不満', 'ふまん', 'fuman',
                    'クソ', 'くそ', 'kuso',
                    'だめ', 'ダメ', 'dame'
                ],
                'patterns': [r'！！+', r'💢', r'怒$', r'ムカ'],
                'weight': 1.3
            },
            'surprised': {
                'keywords': [
                    '驚', 'おどろ', 'odoro',
                    'びっくり', 'ビックリ', 'bikkuri',
                    'すごい', 'スゴイ', 'sugoi',
                    'えっ', 'エッ', 'e',
                    'まじ', 'マジ', 'maji',
                    '信じられない', 'しんじられない', 'shinjirarenai',
                    '本当', 'ほんとう', 'hontou',
                    'やば', 'ヤバ', 'yaba',
                    'うそ', 'ウソ', '嘘', 'uso',
                    'なんと', 'ナント', 'nanto',
                    'まさか', 'マサカ', 'masaka',
                    # 新規追加
                    '意外', 'いがい', 'igai',
                    '予想外', 'よそうがい', 'yosougai',
                    '衝撃', 'しょうげき', 'shougeki',
                    'ショック', 'shock', 'しょっく',
                    '想定外', 'そうていがい', 'souteigai',
                    '仰天', 'ぎょうてん', 'gyouten'
                ],
                'patterns': [r'[!?！？]+', r'。。+', r'ええ[!?！？]'],
                'weight': 1.1
            }
        }
        
        # 文脈による感情判定用のフレーズ
        self.context_phrases = {
            'happy': [
                'よかった', '楽しみ', '期待', '頑張', 'がんば', '応援',
                '成功', 'せいこう', '達成', 'たっせい', '勝利', 'しょうり',
                '祝福', 'しゅくふく', 'おめでとう', 'congratulations'
            ],
            'sad': [
                '残念', 'ざんねん', '悔しい', 'くやしい', '寂しい',
                '心配', 'しんぱい', '不安', 'ふあん', '困った', 'こまった',
                '落胆', 'らくたん', '失望', 'しつぼう',
                # 🎭 伝統工芸関連の悲しい文脈
                '深刻な課題', 'しんこくなかだい', '後継者がいない', 'こうけいしゃがいない',
                '技術が消える', 'ぎじゅつがきえる', '職人が減る', 'しょくにんがへる',
                '伝統がなくなる', 'でんとうがなくなる', '廃れてしまう', 'すたれてしまう'
            ],
            'angry': [
                '許せない', 'ゆるせない', '納得いかない', 'なっとくいかない',
                '理解できない', 'りかいできない', '腹が立つ', 'はらがたつ',
                '不公平', 'ふこうへい', '不当', 'ふとう',
                '文句', 'もんく', '抗議', 'こうぎ', '反対', 'はんたい'
            ],
            'surprised': [
                '知らなかった', 'しらなかった', '初めて', 'はじめて',
                '予想外', 'よそうがい', '想定外', 'そうていがい',
                '驚き', 'おどろき', '発見', 'はっけん'
            ]
        }
        
    def analyze_emotion(self, text: str) -> Tuple[str, float]:
        """
        テキストから感情を分析(改善版)
        Returns: (emotion, confidence)
        """
        if not text:
            return 'neutral', 0.5
            
        # テキストの前処理
        text_lower = text.lower()
        text_normalized = self._normalize_text(text)
        
        # 各感情のスコアを計算
        scores: Dict[str, float] = {
            'happy': 0.0,
            'sad': 0.0,
            'angry': 0.0,
            'surprised': 0.0,
            'neutral': 0.0
        }
        
        # キーワードマッチング
        for emotion, config in self.emotion_keywords.items():
            # キーワードチェック
            for keyword in config['keywords']:
                if keyword in text_normalized:
                    scores[emotion] += 2.0 * config['weight']
                    
            # パターンチェック
            for pattern in config['patterns']:
                if re.search(pattern, text):
                    scores[emotion] += 1.0 * config['weight']
        
        # 文脈フレーズのチェック
        for emotion, phrases in self.context_phrases.items():
            for phrase in phrases:
                if phrase in text_normalized:
                    scores[emotion] += 0.5
        
        # 文の長さによる調整(短い文は感情が強い傾向)
        if len(text) < 10 and max(scores.values()) > 0:
            max_emotion = max(scores, key=scores.get)
            scores[max_emotion] *= 1.2
        
        # 感情強度の判定
        max_score = max(scores.values())
        
        if max_score < 1.0:
            return 'neutral', 0.5
            
        # 最高スコアの感情を選択
        detected_emotion = max(scores, key=scores.get)
        confidence = min(scores[detected_emotion] / 10.0, 1.0)
        
        # 複数の感情が競合する場合の処理
        sorted_emotions = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_emotions) > 1:
            # 2番目に高いスコアとの差が小さい場合は信頼度を下げる
            if sorted_emotions[0][1] - sorted_emotions[1][1] < 1.0:
                confidence *= 0.8
        
        return detected_emotion, confidence
        
    def _normalize_text(self, text: str) -> str:
        """テキストの正規化"""
        # 記号やスペースを除去
        text = re.sub(r'[^\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\w\s]', '', text)
        # 全角英数字を半角に変換
        text = text.translate(str.maketrans('０１２３４５６７８９ＡＢＣＤＥＦ', '0123456789ABCDEF'))
        return text.lower()

# EmotionAnalyzerのインスタンス化
emotion_analyzer = EmotionAnalyzer()

# ====== 【追加箇所1】Live2D対応の感情定義 ======
VALID_EMOTIONS = [
    'neutral', 'happy', 'sad', 'angry', 'surprise',
    'dangerquestion', 'responseready', 'start'
]

# ====== グローバル変数 ======
# OpenAIクライアント
client = None

# RAGChatbot
chatbot = None

# セッションデータ(メモリ内保存)
session_data = {}

# 訪問者データ(永続化用)
visitor_data = {}

# 感情履歴管理
emotion_histories = defaultdict(lambda: deque(maxlen=50))
mental_state_histories = defaultdict(lambda: deque(maxlen=30))
emotion_transition_stats = defaultdict(lambda: defaultdict(int))

# キャッシュ(会話履歴用)
conversation_cache = {}
audio_cache = {}

# ====== クイズシステムデータ ======
QUIZ_DATA = {
    'ja': [
        {
            'question': '京友禅を確立したとされる人物は誰でしょう?',
            'options': [
                'A) 宮崎友禅斎',
                'B) 野々村仁清',
                'C) 本阿弥光悦'
            ],
            'correct': 0,
            'explanation': '江戸時代の元禄期に、扇絵師だった宮崎友禅斎が確立した染色技法です。彼の名前が「友禅染」の由来となっています!'
        },
        {
            'question': '京友禅の最大の特徴である技法は何でしょう?',
            'options': [
                'A) 型紙を使った捺染',
                'B) 糸目糊による手描き染色',
                'C) 絞り染め'
            ],
            'correct': 1,
            'explanation': '細い筒から糊を絞り出して輪郭線を描き、色が混ざらないようにする「糸目糊」が京友禅の代表的な技法です。繊細で優美な表現が可能になります✨'
        },
        {
            'question': '京友禅の色彩や図柄の特徴として正しいものはどれ?',
            'options': [
                'A) 原色を多用した大胆な柄',
                'B) 藍色一色のシンプルな柄',
                'C) 優美で雅な多色使いの柄'
            ],
            'correct': 2,
            'explanation': '京友禅は、京都の雅な文化を反映した繊細で優美な色彩と、四季の草花や御所車などの伝統的な図柄が特徴です。多彩な色を使った華やかさが魅力です🌸'
        }
    ],
    'en': [
        {
            'question': 'Who is credited with establishing Kyo-Yuzen?',
            'options': [
                'A) Miyazaki Yuzensai',
                'B) Nonomura Ninsei',
                'C) Hon\'ami Koetsu'
            ],
            'correct': 0,
            'explanation': 'It was established by Miyazaki Yuzensai, a fan painter during the Genroku period of the Edo era. His name became the origin of "Yuzen-zome"!'
        },
        {
            'question': 'What is the main technique characteristic of Kyo-Yuzen?',
            'options': [
                'A) Stencil dyeing',
                'B) Hand-painted dyeing with paste resist',
                'C) Tie-dyeing'
            ],
            'correct': 1,
            'explanation': 'The "itome-nori" (paste resist) technique, where paste is squeezed from a thin tube to draw outlines preventing color mixing, is the representative technique of Kyo-Yuzen. It enables delicate and elegant expressions✨'
        },
        {
            'question': 'Which correctly describes the color and pattern characteristics of Kyo-Yuzen?',
            'options': [
                'A) Bold patterns with primary colors',
                'B) Simple patterns in indigo only',
                'C) Elegant multi-colored patterns'
            ],
            'correct': 2,
            'explanation': 'Kyo-Yuzen features delicate and elegant colors reflecting Kyoto\'s refined culture, and traditional patterns like seasonal flowers and imperial carriages. The splendor of diverse colors is its charm🌸'
        }
    ]
}

# クイズセッション管理
quiz_sessions = {}

# CoeFontクライアント
coe_font_client = None
use_coe_font = False

# Azure Speech Serviceクライアント
azure_speech_client = None
use_azure_speech = False

# SpeechProcessor (音声認識)
speech_processor = None

# ====== CoeFontの音声合成クラス ======
class CoeFontClient:
    """CoeFont音声合成クライアント"""
    
    def __init__(self, access_key=None, access_secret=None, coefont_id=None):
        self.access_key = access_key
        self.access_secret = access_secret
        self.coefont_id = coefont_id
        self.base_url = "https://api.coefont.ai/v2"
        
    def test_connection(self):
        """接続テスト"""
        if not self.access_key or not self.access_secret:
            return False
            
        headers = {
            'X-Api-Key': self.access_key,
            'X-Api-Secret': self.access_secret
        }
        
        try:
            response = requests.get(f"{self.base_url}/voices", headers=headers)
            return response.status_code == 200
        except:
            return False
    
    def generate_voice(self, text, emotion='neutral', speed=1.0):
        """音声生成"""
        if not self.access_key or not self.access_secret or not self.coefont_id:
            raise ValueError("CoeFont APIの認証情報が設定されていません")
            
        headers = {
            'X-Api-Key': self.access_key,
            'X-Api-Secret': self.access_secret,
            'Content-Type': 'application/json'
        }
        
        # 感情パラメータの調整
        emotion_params = self._get_emotion_params(emotion)
        
        data = {
            'text': text,
            'voice_id': self.coefont_id,
            'speed': speed,
            **emotion_params
        }
        
        response = requests.post(
            f"{self.base_url}/text-to-speech",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            return response.content
        else:
            raise Exception(f"CoeFont API Error: {response.status_code} - {response.text}")
    
    def _get_emotion_params(self, emotion):
        """感情に応じたパラメータを設定"""
        emotion_map = {
            'happy': {'pitch': 1.1, 'volume': 1.1},
            'sad': {'pitch': 0.9, 'volume': 0.9},
            'angry': {'pitch': 1.0, 'volume': 1.2},
            'surprised': {'pitch': 1.2, 'volume': 1.1},
            'neutral': {'pitch': 1.0, 'volume': 1.0}
        }
        return emotion_map.get(emotion, emotion_map['neutral'])

# ====== Azure Speech Serviceの音声合成クラス ======
class AzureSpeechClient:
    """Azure Speech Service音声合成クライアント"""
    
    def __init__(self, speech_key=None, speech_region=None, voice_name=None):
        self.speech_key = speech_key
        self.speech_region = speech_region
        self.voice_name = voice_name or 'ja-JP-NanamiNeural'
        
    def test_connection(self):
        """接続テスト"""
        if not self.speech_key or not self.speech_region:
            return False
        try:
            speech_config = speechsdk.SpeechConfig(
                subscription=self.speech_key, 
                region=self.speech_region
            )
            return True
        except Exception as e:
            print(f"Azure Speech接続エラー: {e}")
            return False
    
    def generate_voice(self, text, voice_name=None, emotion='neutral', speed=1.0):
        """音声生成（REST API使用）
        
        主な日本語音声:
        - 'ja-JP-NanamiNeural' (女性、優しい声) ← デフォルト
        - 'ja-JP-AoiNeural' (女性、明るい声)
        - 'ja-JP-MayuNeural' (女性、落ち着いた声)
        - 'ja-JP-ShioriNeural' (女性、若い声)
        """
        if not self.speech_key or not self.speech_region:
            raise ValueError("Azure Speech APIの認証情報が設定されていません")
        
        # 音声名の決定
        voice = voice_name or self.voice_name
        
        # 感情スタイルのマッピング
        emotion_styles = {
            'happy': 'cheerful',
            'sad': 'sad',
            'angry': 'angry',
            'surprised': 'excited',
            'neutral': 'general',
            'start': 'cheerful',
            'dangerquestion': 'serious',
            'neutraltalking': 'general',
            'responseready': 'general'
        }
        style = emotion_styles.get(emotion, 'general')
        
        # スピード調整
        speech_rate = f"{int((speed - 1) * 100):+d}%"
        
        # 抑揚の強さを設定（感情によって変える）
        style_degree = "2"  # 1.0（デフォルト）～ 2.0（最大）、抑揚を強くする
        if emotion in ['happy', 'surprised', 'start']:
            style_degree = "2"  # 明るい感情は抑揚を最大に
        elif emotion in ['sad', 'angry']:
            style_degree = "1.8"  # 悲しみや怒りも抑揚を強めに
        else:
            style_degree = "1.5"  # 通常は1.5倍
        
        # SSML（音声合成マークアップ）を作成
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
               xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="ja-JP">
            <voice name="{voice}">
                <mstts:express-as style="{style}" styledegree="{style_degree}">
                    <prosody rate="{speech_rate}" pitch="+5%">
                        {text}
                    </prosody>
                </mstts:express-as>
            </voice>
        </speak>
        """
        
        # Azure Speech REST APIを使用（SDKの代わり）
        # ⚠️ SDKはAWS環境で「Error 2176」が発生するため、REST APIを使用
        try:
            import requests
            
            # REST API エンドポイント
            url = f"https://{self.speech_region}.tts.speech.microsoft.com/cognitiveservices/v1"
            
            headers = {
                'Ocp-Apim-Subscription-Key': self.speech_key,
                'Content-Type': 'application/ssml+xml',
                'X-Microsoft-OutputFormat': 'riff-24khz-16bit-mono-pcm',  # WAV形式
                'User-Agent': 'REI-Avatar-System'
            }
            
            response = requests.post(url, headers=headers, data=ssml.encode('utf-8'), timeout=30)
            
            if response.status_code == 200:
                audio_data = response.content
                print(f"✅ Azure音声生成成功 (REST API): {len(audio_data)} bytes")
                return audio_data
            else:
                error_msg = f"Azure Speech REST API Error: {response.status_code} - {response.text}"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            print(f"❌ Azure音声生成エラー (REST API): {e}")
            import traceback
            traceback.print_exc()
            raise

# ====== 【修正箇所】理解度レベル管理システム ======
def calculate_relationship_level(conversation_count):
    """会話回数から理解度レベルを判定"""
    if conversation_count < 2:
        return {'level': 0, 'style': 'formal', 'name': '-'}
    elif conversation_count < 4:
        return {'level': 1, 'style': 'casual_polite', 'name': 'Level 1'}
    elif conversation_count < 6:
        return {'level': 2, 'style': 'friendly', 'name': 'Level 2'}
    elif conversation_count < 8:
        return {'level': 3, 'style': 'close', 'name': 'Level 3'}
    else:
        return {'level': 4, 'style': 'best_friend', 'name': 'MAX'}

def get_relationship_adjusted_greeting(language, relationship_style):
    """関係性レベルに応じた挨拶を生成"""
    greetings = {
        'ja': {
            'formal': "はじめまして！手描き京友禅職人のレイです！私は糸目のり置きという工程を専門にしています。何でも質問してくださいね！",
            'polite': "こんにちは!また会えて嬉しいです。今日はどんなお話をしましょうか?",
            'friendly': "やっほー!会いたかったよ〜!今日も楽しくお話しようね!",
            'casual': "おっす!元気にしてた?なんか面白い話ある?"
        },
        'en': {
            'formal': "Hello! I'm Rei. It's a pleasure to meet you.",
            'polite': "Hello again! It's nice to see you. What would you like to talk about today?",
            'friendly': "Hey there! I missed you! Let's have fun chatting today!",
            'casual': "Yo! How've you been? Got any interesting stories?"
        }
    }
    
    return greetings.get(language, greetings['ja']).get(relationship_style, greetings[language]['formal'])

# ====== 初期化処理 ======
def initialize_system():
    """システムの初期化"""
    global client, chatbot, coe_font_client, use_coe_font, azure_speech_client, use_azure_speech, speech_processor
    
    print("🚀 システム初期化中...")
    
    # OpenAI API初期化
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️ 警告: OPENAI_API_KEYが設定されていません")
    else:
        client = OpenAI(api_key=api_key)
        print("✅ OpenAI API初期化完了")
    
    # SpeechProcessor初期化（音声認識用）
    try:
        speech_processor = SpeechProcessor()
        print("✅ SpeechProcessor初期化完了")
    except Exception as e:
        print(f"⚠️ SpeechProcessor初期化失敗: {e}")
    
    # 🆕 Azure Speech Service初期化（日本語用 - 最優先）
    azure_key = os.getenv('AZURE_SPEECH_KEY')
    azure_region = os.getenv('AZURE_SPEECH_REGION', 'japaneast')
    azure_voice = os.getenv('AZURE_VOICE_NAME', 'ja-JP-NanamiNeural')
    
    if azure_key and azure_region:
        azure_speech_client = AzureSpeechClient(azure_key, azure_region, azure_voice)
        if azure_speech_client.test_connection():
            use_azure_speech = True
            print(f"✅ Azure Speech Service初期化完了 (音声: {azure_voice})")
        else:
            print("⚠️ Azure Speech Service接続テスト失敗")
    else:
        print("ℹ️ Azure Speech Serviceは設定されていません")
    
    # CoeFont API初期化（フォールバック用 - Azureが無い場合のみ）
    coefont_enabled = os.getenv('COEFONT_ENABLED', 'false').lower() == 'true'
    coefont_key = os.getenv('COEFONT_ACCESS_KEY')
    coefont_secret = os.getenv('COEFONT_ACCESS_SECRET')
    coefont_id = os.getenv('COEFONT_VOICE_ID')
    
    # Azureが使えない場合のみCoeFontを初期化
    if not use_azure_speech and coefont_enabled and coefont_key and coefont_secret and coefont_id:
        coe_font_client = CoeFontClient(coefont_key, coefont_secret, coefont_id)
        if coe_font_client.test_connection():
            use_coe_font = True
            print("✅ CoeFont API初期化完了（フォールバック）")
        else:
            print("⚠️ CoeFont API接続テスト失敗")
    else:
        if use_azure_speech:
            print("ℹ️ Azure Speech Serviceを使用するため、CoeFontは無効化されています")
        else:
            print("ℹ️ CoeFont APIは設定されていません")
    
    # RAGChatbot初期化
    try:
        chatbot = RAGSystem()
        print("✅ RAGChatbot初期化完了")
    except Exception as e:
        print(f"❌ RAGChatbot初期化エラー: {e}")
    
    print("🎉 システム初期化完了")
    print(f"📊 音声エンジン状況: Azure={use_azure_speech}, CoeFont={use_coe_font}, OpenAI TTS=常に利用可能")

# ====== ユーティリティ関数 ======
def get_session_data(session_id):
    """セッションデータを取得(なければ作成)"""
    if session_id not in session_data:
        session_data[session_id] = {
            'conversation_history': [],
            'interaction_count': 0,
            'visitor_id': None,
            'language': 'ja',
            'emotion_history': [],
            'question_count': 0,
            'mental_state': {
                'stress_level': 0,
                'engagement_level': 0.5,
                'conversation_depth': 0
            },
            'selected_suggestions': [],
            'current_emotion': 'neutral',
            'relationship_style': 'formal'
        }
    return session_data[session_id]

def get_visitor_data(visitor_id):
    """訪問者データを取得(なければ作成)"""
    if visitor_id not in visitor_data:
        visitor_data[visitor_id] = {
            'first_visit': datetime.now().isoformat(),
            'last_visit': datetime.now().isoformat(),
            'visit_count': 1,
            'total_conversations': 0,
            'topics_discussed': [],
            'personality_traits': {},
            'relationship_level': 0,
            'selected_suggestions': set()
        }
    return visitor_data[visitor_id]

# ====== 音声生成関数 ======
def generate_audio_by_language(text, language='ja', emotion_params='neutral'):
    """言語に応じた音声生成（Azure優先）"""
    # 音声キャッシュのチェック
    cache_key = hashlib.md5(f"{text}_{language}_{emotion_params}".encode()).hexdigest()
    if cache_key in audio_cache:
        print(f"🎵 音声キャッシュヒット: {cache_key[:8]}")
        return audio_cache[cache_key]
    
    try:
        # 🆕 日本語の場合、Azure Speech Serviceを最優先
        if language == 'ja' and use_azure_speech:
            print(f"🎤 Azure Speech Serviceで音声生成中... (感情: {emotion_params})")
            audio_content = azure_speech_client.generate_voice(
                text, 
                emotion=emotion_params,
                speed=1.0
            )
            
            # WAVファイルとして一時保存
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                tmp_file.write(audio_content)
                tmp_path = tmp_file.name
            
            # Base64エンコード
            with open(tmp_path, 'rb') as f:
                audio_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            # 一時ファイル削除
            os.unlink(tmp_path)
            
            print(f"✅ Azure音声生成成功: {len(audio_content)} バイト")
            
        # フォールバック: 日本語 + CoeFont（Azureが無い場合のみ）
        elif language == 'ja' and use_coe_font:
            print(f"🎤 CoeFont APIで音声生成中... (感情: {emotion_params})")
            audio_content = coe_font_client.generate_voice(text, emotion=emotion_params)
            
            # WAVファイルとして保存
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                tmp_file.write(audio_content)
                tmp_path = tmp_file.name
            
            # Base64エンコード
            with open(tmp_path, 'rb') as f:
                audio_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            os.unlink(tmp_path)
            print(f"✅ CoeFont音声生成成功")
            
        # その他の言語（英語など） → OpenAI TTS
        else:
            print(f"🎤 OpenAI TTSで音声生成中... (言語: {language})")
            if not client:
                print("⚠️ OpenAI clientが初期化されていません")
                return None
                
            voice = 'nova' if language == 'en' else 'alloy'
            
            speech_response = client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            
            # MP3をBase64エンコード
            audio_content = speech_response.content
            audio_base64 = base64.b64encode(audio_content).decode('utf-8')
            print(f"✅ OpenAI TTS音声生成成功")
        
        # キャッシュに保存(最大100件)
        if len(audio_cache) >= 100:
            # 古いエントリを削除
            oldest_key = next(iter(audio_cache))
            del audio_cache[oldest_key]
        
        audio_cache[cache_key] = audio_base64
        
        # 使用した音声エンジンをログ出力
        engine = 'Azure Speech' if (language == 'ja' and use_azure_speech) else \
                 'CoeFont' if (language == 'ja' and use_coe_font) else \
                 'OpenAI TTS'
        print(f"🎵 音声生成完了: {cache_key[:8]} (エンジン: {engine})")
        
        return audio_base64
        
    except Exception as e:
        print(f"❌ 音声生成エラー: {e}")
        import traceback
        traceback.print_exc()
        return None

# ====== カスタム応答調整 ======
def adjust_response_style(response, language='ja', relationship_style='formal'):
    """関係性レベルに応じて応答スタイルを調整（正規表現対応版）"""
    import re
    
    if language == 'ja':
        if relationship_style == 'casual':
            # カジュアルな日本語に変換
            response = response.replace("です。", "だよ。")
            response = response.replace("でしょう。", "だよね。")
            response = response.replace("ですか?", "?")
            # 🔧 修正: 「ます。」の適切な処理（正規表現不使用、安全な置換のみ）
            # 問題: 「なってしまいます」→「なってしまいるよ」を防ぐ
            # 解決: 単純な置換は削除（フォーマル体のまま維持）
        elif relationship_style == 'friendly':
            # フレンドリーな日本語
            response = response.replace("です。", "だよ〜。")
            # 🔧 修正: 「ます。」の適切な処理
            # 問題: 「なってしまいます」→「なってしまいるね!」を防ぐ
            # 解決: 単純な置換は削除（フォーマル体のまま維持）
    elif language == 'en':
        if relationship_style == 'casual':
            # カジュアルな英語に変換
            try:
                translation = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system", 
                            "content": "Convert this text to casual, friendly English. Use contractions and informal language. Maintain the casual, friendly tone."
                        },
                        {
                            "role": "user", 
                            "content": response
                        }
                    ],
                    temperature=0.7,
                    max_tokens=100
                )
                return translation.choices[0].message.content
            except Exception as e:
                print(f"翻訳エラー: {e}")
                response = response.replace("だよね", ", right?")
                response = response.replace("だよ", "")
                response = response.replace("じゃん", ", you know")
                response = response.replace("だし", ", and")
    return response

# ====== 【修正箇所2】改善された感情分析関数(9種類対応) ======
def analyze_emotion(text):
    """
    テキストから感情を分析(9種類対応)
    Returns: 感情文字列 ('neutral', 'happy', 'sad', 'angry', 'surprise', 
             'dangerquestion', 'responseready', 'start')
    """
    if not text:
        return 'neutral'
    
    text_lower = text.lower().strip()
    
    # 1. DangerQuestion判定(不適切な質問) - 最優先
    danger_keywords = [
        # 日本語
        'セクシー', 'エロ', '裸', '脱', '下着', '胸', 'おっぱい',
        'パンツ', 'ブラ', 'きわどい', 'えっち', 'いやらしい',
        # 英語
        'sexy', 'nude', 'naked', 'breast', 'underwear', 'erotic',
        'strip', 'panties', 'bra', 'inappropriate'
    ]
    
    if any(keyword in text_lower for keyword in danger_keywords):
        print(f"🚫 DangerQuestion detected: {text[:30]}...")
        return 'dangerquestion'
    
    # 2. ResponseReady判定(真剣な質問)
    serious_indicators = 0
    
    # 質問マーカーチェック
    question_markers = ['?', '?', 'どう', 'なぜ', 'なに', '教えて', 
                       'how', 'why', 'what', 'explain']
    if any(marker in text_lower for marker in question_markers):
        serious_indicators += 1
    
    # 長文チェック(50文字以上)
    if len(text) > 50:
        serious_indicators += 1
    
    # 専門用語チェック
    technical_terms = ['方法', '手順', '技術', '仕組み', 'やり方', 
                      '原理', 'システム', '詳しく', '具体的']
    if any(term in text_lower for term in technical_terms):
        serious_indicators += 1
    
    if serious_indicators >= 2:
        print(f"📚 ResponseReady detected: {text[:30]}...")
        return 'responseready'
    
    # 3. 基本感情の判定
    # Happy
    happy_words = ['嬉しい', 'うれしい', '楽しい', 'たのしい', 'わくわく',
                   'やった', '最高', 'happy', 'glad', 'excited', 'joy', 'great']
    if any(word in text_lower for word in happy_words):
        return 'happy'
    
    # Sad
    sad_words = ['悲しい', 'かなしい', '寂しい', 'さみしい', '辛い', 'つらい',
                 '泣', '涙', 'sad', 'lonely', 'cry', 'tear', 'depressed']
    if any(word in text_lower for word in sad_words):
        return 'sad'
    
    # Angry
    angry_words = ['怒', 'おこ', 'むかつく', 'イライラ', '腹立', 'ムカ',
                   'angry', 'mad', 'furious', 'annoyed', 'pissed']
    if any(word in text_lower for word in angry_words):
        return 'angry'
    
    # Surprise
    surprise_words = ['驚', 'びっくり', 'すごい', 'まさか', 'えっ', 'わっ',
                      'surprise', 'amazing', 'wow', 'incredible', 'unbelievable']
    if any(word in text_lower for word in surprise_words):
        return 'surprise'
    
    # デフォルト
    return 'neutral'

# ====== 【追加箇所4】感情検証ヘルパー関数 ======
def validate_emotion(emotion):
    """感情の検証と正規化"""
    if not emotion or emotion not in VALID_EMOTIONS:
        print(f"⚠️ 無効な感情 '{emotion}' → 'neutral'にフォールバック")
        return 'neutral'
    return emotion.lower()

# ====== 【修正1】generate_prioritized_suggestions()関数の完全置き換え ======
def generate_prioritized_suggestions(session_info, visitor_info, relationship_style, language='ja'):
    """
    static_qa_data.pyを使った段階別サジェスチョン生成
    
    【修正理由】
    - static_qa_data.pyの段階別システムを活用
    - suggestionと回答キーの完全一致を保証
    - 重複排除の自動化
    
    Args:
        session_info: セッション情報
        visitor_info: 訪問者情報
        relationship_style: 関係性スタイル
        language: 言語コード ('ja' or 'en')
    
    Returns:
        list: サジェスチョンリスト(最大3個)
    """
    try:
        # static_qa_data.pyから必要な関数をインポート
        from modules.static_qa_data import get_staged_suggestions_multilang, get_current_stage
        
        # 選択済みサジェスチョンを取得(リスト形式に統一)
        selected_suggestions = []
        
        # セッション情報から取得
        if session_info and 'selected_suggestions' in session_info:
            session_selected = session_info.get('selected_suggestions', [])
            if isinstance(session_selected, list):
                selected_suggestions.extend(session_selected)
            elif isinstance(session_selected, set):
                selected_suggestions.extend(list(session_selected))
        
        # 訪問者情報から取得
        if visitor_info and 'selected_suggestions' in visitor_info:
            visitor_selected = visitor_info.get('selected_suggestions', set())
            if isinstance(visitor_selected, set):
                selected_suggestions.extend(list(visitor_selected))
            elif isinstance(visitor_selected, list):
                selected_suggestions.extend(visitor_selected)
        
        # 重複を除去
        selected_suggestions = list(set(selected_suggestions))
        
        # 現在の段階を判定(選択済みサジェスチョン数から自動判定)
        suggestions_count = len(selected_suggestions)
        current_stage = get_current_stage(suggestions_count)
        
        print(f"[DEBUG] Suggestions count: {suggestions_count}, Stage: {current_stage}")
        print(f"[DEBUG] Selected suggestions: {selected_suggestions}")
        
        # 段階別サジェスチョンを取得
        suggestions = get_staged_suggestions_multilang(
            stage=current_stage,
            language=language,
            selected_suggestions=selected_suggestions
        )
        
        print(f"[DEBUG] Generated suggestions: {suggestions}")
        
        return suggestions
        
    except Exception as e:
        print(f"❌ サジェスチョン生成エラー: {e}")
        import traceback
        traceback.print_exc()
        
        # エラー時のフォールバック
        if language == 'en':
            return ["Tell me about Kyo-Yuzen", "What kind of works do you create?", "Explain the Yuzen process"]
        else:
            return ["京友禅について教えて", "どんな作品を作っていますか?", "友禅の工程を説明してください"]

def calculate_mental_state(session_info):
    """精神状態の計算(感情履歴ベース)"""
    emotion_history = session_info.get('emotion_history', [])
    
    if not emotion_history:
        return {
            'stress_level': 0,
            'engagement_level': 0.5,
            'conversation_depth': 0
        }
    
    # 最近の感情を重視
    recent_emotions = emotion_history[-10:]
    
    # ストレスレベル計算
    negative_emotions = ['sad', 'angry']
    stress_level = sum(1 for e in recent_emotions if e.get('emotion') in negative_emotions) / len(recent_emotions)
    
    # エンゲージメントレベル計算
    active_emotions = ['happy', 'surprised', 'angry']
    engagement_level = sum(1 for e in recent_emotions if e.get('emotion') in active_emotions) / len(recent_emotions)
    
    # 会話の深さ
    conversation_depth = min(session_info.get('interaction_count', 0) / 20, 1.0)
    
    return {
        'stress_level': stress_level,
        'engagement_level': engagement_level,
        'conversation_depth': conversation_depth
    }

def update_visitor_data(visitor_id, session_info):
    """訪問者データを更新"""
    if visitor_id and visitor_id in visitor_data:
        v_data = visitor_data[visitor_id]
        
        # 訪問回数と会話数を更新
        v_data['last_visit'] = datetime.now().isoformat()
        v_data['total_conversations'] += session_info.get('interaction_count', 0)
        
        # トピックの更新
        for msg in session_info.get('conversation_history', []):
            if 'content' in msg:
                # 簡単なトピック抽出(実装は簡略化)
                if '友禅' in msg['content']:
                    if '友禅' not in v_data['topics_discussed']:
                        v_data['topics_discussed'].append('友禅')
        
        # 関係性レベルの更新
        current_level = calculate_relationship_level(v_data['total_conversations'])['level']
        if current_level > v_data['relationship_level']:
            v_data['relationship_level'] = current_level
        
        # 関係性スタイルの更新
        v_data['relationship_style'] = session_info.get('relationship_style', 'formal')
        
        # 選択されたサジェスチョンの更新
        for suggestion in session_info.get('selected_suggestions', []):
            v_data['selected_suggestions'].add(suggestion)

def update_emotion_history(session_id, emotion, mental_state=None):
    """🎯 感情履歴を更新"""
    session_info = get_session_data(session_id)
    
    # 現在の感情を更新
    previous_emotion = session_info.get('current_emotion', 'neutral')
    session_info['current_emotion'] = emotion
    session_info['emotion_history'].append({
        'emotion': emotion,
        'timestamp': datetime.now().isoformat(),
        'interaction_count': session_info['interaction_count']
    })
    
    # 感情遷移の統計を更新
    emotion_transition_stats[previous_emotion][emotion] += 1
    
    # 全体の感情履歴に追加
    if session_id in emotion_histories:
        emotion_histories[session_id].append({
            'emotion': emotion,
            'timestamp': datetime.now().isoformat()
        })
    
    # 精神状態も記録
    if mental_state:
        session_info['mental_state'] = mental_state
        if session_id in mental_state_histories:
            mental_state_histories[session_id].append({
                'state': mental_state,
                'timestamp': datetime.now().isoformat()
            })

def normalize_question(question):
    """質問を正規化(重複判定用)"""
    return question.lower().replace('?', '').replace('?', '').replace('。', '').replace('、', '').replace('!', '').replace('!', '').strip()

def print_cache_stats():
    """キャッシュ統計を表示"""
    print(f"📊 キャッシュ統計:")
    print(f"  - 会話キャッシュ: {len(conversation_cache)} エントリ")
    print(f"  - 音声キャッシュ: {len(audio_cache)} エントリ")
    print(f"  - アクティブセッション: {len(session_data)}")
    print(f"  - 登録訪問者: {len(visitor_data)}")

# ====== Flaskルート ======
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health_check():
    """ヘルスチェックエンドポイント"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_sessions': len(session_data),
        'visitors': len(visitor_data),
        'cache_size': {
            'conversation': len(conversation_cache),
            'audio': len(audio_cache)
        },
        'services': {
            'openai': client is not None,
            'rag': chatbot is not None,
            'coefont': use_coe_font
        }
    })

@app.route('/api/coefont/status')
def coefont_status():
    """CoeFont APIの状態を確認"""
    status = {
        'enabled': use_coe_font,
        'configured': coe_font_client is not None,
        'access_key_set': bool(coe_font_client.access_key),
        'access_secret_set': bool(coe_font_client.access_secret),
        'voice_id_set': bool(coe_font_client.coefont_id),
        'test_connection': False,
        'error_message': None
    }
    
    # 接続テストを実行
    if use_coe_font:
        try:
            test_result = coe_font_client.test_connection()
            status['test_connection'] = test_result
        except Exception as e:
            status['error_message'] = str(e)
    
    return jsonify(status)

# ====== 🧠 会話記憶システムのデバッグエンドポイント ======
@app.route('/visitor-stats')
def show_visitor_stats():
    """訪問者統計を表示"""
    return jsonify({
        'total_visitors': len(visitor_data),
        'active_sessions': len(session_data),
        'visitor_summary': [
            {
                'visitor_id': vid,
                'visit_count': vdata.get('visit_count', 0),
                'total_conversations': vdata.get('total_conversations', 0),
                'relationship_level': vdata.get('relationship_level', 0),
                'topics_discussed': vdata.get('topics_discussed', [])
            }
            for vid, vdata in visitor_data.items()
        ]
    })

# 🎯 新しいエンドポイント:感情統計
@app.route('/emotion-stats')
def show_emotion_stats():
    """感情統計を表示"""
    # セッションごとの感情分布
    session_emotions = {}
    for sid, sdata in session_data.items():
        if 'emotion_history' in sdata:
            emotions = [e['emotion'] for e in sdata['emotion_history']]
            session_emotions[sid] = {
                'total': len(emotions),
                'distribution': dict(defaultdict(int, {e: emotions.count(e) for e in set(emotions)})),
                'current': sdata.get('current_emotion', 'neutral')
            }
    
    # 感情遷移の統計
    transition_matrix = {}
    for from_emotion, to_emotions in emotion_transition_stats.items():
        transition_matrix[from_emotion] = dict(to_emotions)
    
    return jsonify({
        'session_emotions': session_emotions,
        'emotion_transitions': transition_matrix,
        'total_sessions': len(session_data),
        'active_emotions': {
            sid: sdata.get('current_emotion', 'neutral') 
            for sid, sdata in session_data.items()
        }
    })

# 🎯 新しいエンドポイント:精神状態
@app.route('/mental-state/<session_id>')
def show_mental_state(session_id):
    """特定セッションの精神状態を表示"""
    if session_id not in session_data:
        return jsonify({'error': 'Session not found'}), 404
    
    session_info = session_data[session_id]
    mental_state = session_info.get('mental_state', {})
    
    # 精神状態の履歴
    history = []
    if session_id in mental_state_histories:
        history = list(mental_state_histories[session_id])[-10:]  # 最新10件
    
    return jsonify({
        'session_id': session_id,
        'current_mental_state': mental_state,
        'emotion': session_info.get('current_emotion', 'neutral'),
        'relationship_level': session_info.get('relationship_style', 'formal'),
        'interaction_count': session_info.get('interaction_count', 0),
        'history': history
    })

@app.route('/api/reward-image')
def get_reward_image():
    """クイズ報酬の待ち受け画像を提供"""
    try:
        # 画像ファイルのパスを指定
        image_path = os.path.join(app.static_folder, 'images', 'rei_wallpaper.png')
        
        if not os.path.exists(image_path):
            # 画像が存在しない場合はダミー画像を生成
            if Image:
                img = Image.new('RGB', (1080, 1920), color=(255, 182, 193))
                draw = ImageDraw.Draw(img)
                
                # テキストを描画
                text = "REI\nKYO YUZEN\nMaster Certificate"
                try:
                    font = ImageFont.truetype("arial.ttf", 80)
                except:
                    font = ImageFont.load_default()
                
                # テキスト位置を中央に
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                position = ((1080 - text_width) // 2, (1920 - text_height) // 2)
                
                draw.text(position, text, fill=(255, 255, 255), font=font)
                
                # 一時保存
                temp_path = tempfile.mktemp(suffix='.png')
                img.save(temp_path, 'PNG')
                image_path = temp_path
            else:
                # Pillowが利用できない場合
                return jsonify({'error': 'Image generation not available'}), 404
        
        return send_file(
            image_path,
            mimetype='image/png',
            as_attachment=True,
            download_name='REI_Wallpaper.png'
        )
        
    except Exception as e:
        print(f"❌ 画像提供エラー: {e}")
        return jsonify({'error': 'Image not available'}), 404

# ============== WebSocketイベントハンドラー ==============

# 訪問者情報の受信
@socketio.on('visitor_info')
def handle_visitor_info(data):
    session_id = request.sid
    visitor_id = data.get('visitorId')
    visit_data = data.get('visitData', {})
    
    session_info = get_session_data(session_id)
    session_info['visitor_id'] = visitor_id
    
    # 訪問者データの更新
    if visitor_id:
        v_data = get_visitor_data(visitor_id)
        v_data['visit_count'] = visit_data.get('visitCount', 1)
        v_data['last_visit'] = datetime.now().isoformat()
        
        print(f'👤 訪問者情報更新: {visitor_id} (訪問回数: {v_data["visit_count"]})')

# ====== 【修正箇所3】handle_connect関数の修正(9種類感情対応) ======
@socketio.on('connect')
def handle_connect():
    """WebSocket接続時の処理"""
    session_id = request.sid
    visitor_id = request.args.get('visitor_id', str(uuid.uuid4()))
    
    print(f"🔗 新規接続: Session={session_id}, Visitor={visitor_id}")
    
    # セッションデータ初期化
    if session_id not in session_data:
        session_data[session_id] = {
            'visitor_id': visitor_id,
            'first_interaction': True,
            'emotion_history': [],
            'question_count': 0,
            'last_emotion': 'neutral',
            'conversation_start': datetime.now(),
            'language': 'ja',
            'conversation_history': [],
            'interaction_count': 0,
            'mental_state': {
                'stress_level': 0,
                'engagement_level': 0.5,
                'conversation_depth': 0
            },
            'selected_suggestions': [],
            'current_emotion': 'neutral',
            'relationship_style': 'formal'
        }
        
        # 初回接続の場合
        if session_data[session_id]['first_interaction']:
            try:
                # 自己紹介メッセージ
                intro_message = "はじめまして！手描き京友禅職人のレイです！私は糸目のりおきという工程を専門にしています。何でも質問してくださいね！"
                intro_emotion = 'start'  # Startモーション使用
                
                # 感情を検証
                intro_emotion = validate_emotion(intro_emotion)
                
                # 音声生成
                try:
                    audio_data = generate_audio_by_language(
                        intro_message, 
                        'ja', 
                        emotion_params=intro_emotion
                    )
                except Exception as e:
                    print(f"❌ 挨拶音声生成エラー: {e}")
                    audio_data = None
                
                # 初回挨拶データ
                greeting_data = {
                    'message': intro_message,
                    'emotion': intro_emotion,
                    'audio': audio_data,
                    'isGreeting': True,
                    'language': 'ja',
                    'voice_engine': 'azure_speech' if use_azure_speech else ('coe_font' if use_coe_font else 'openai_tts'),
                    'relationshipLevel': 'formal',
                    'mentalState': session_data[session_id]['mental_state']
                }
                
                # サジェスチョン生成
                greeting_data['suggestions'] = generate_prioritized_suggestions(
                    session_data[session_id], 
                    None, 
                    'formal', 
                    'ja'
                )
                
                emit('greeting', greeting_data)
                
                # 感情履歴を更新
                update_emotion_history(session_id, intro_emotion)
                
                # 初回フラグを更新
                session_data[session_id]['first_interaction'] = False
                
            except Exception as e:
                print(f"❌ 挨拶生成エラー: {e}")
                emit('error', {'message': '初期化中にエラーが発生しました'})
    
    else:
        # 既存セッションの場合
        data = get_session_data(session_id)
        language = data["language"]
        
        # 訪問者の関係性レベルを確認
        visitor_info = None
        relationship_style = 'formal'
        if visitor_id and visitor_id in visitor_data:
            visitor_info = visitor_data[visitor_id]
            conversation_count = visitor_info.get('total_conversations', 0)
            rel_info = calculate_relationship_level(conversation_count)
            relationship_style = rel_info['style']
            data['relationship_style'] = relationship_style
        
        print(f'🔌 クライアント再接続: {session_id}, 言語: {language}, 関係性: {relationship_style}')
        
        # 再接続メッセージ
        greeting_message = get_relationship_adjusted_greeting(language, relationship_style)
        greeting_emotion = "happy"
        
        # 感情を検証
        greeting_emotion = validate_emotion(greeting_emotion)
        
        # 感情履歴を更新
        update_emotion_history(session_id, greeting_emotion)
        
        try:
            audio_data = generate_audio_by_language(
                greeting_message, 
                language, 
                emotion_params=greeting_emotion
            )
        except Exception as e:
            print(f"❌ 挨拶音声生成エラー: {e}")
            audio_data = None
        
        greeting_data = {
            'message': greeting_message,
            'emotion': greeting_emotion,
            'audio': audio_data,
            'isGreeting': True,
            'language': language,
            'voice_engine': 'azure_speech' if (use_azure_speech and language == 'ja') else ('coe_font' if (use_coe_font and language == 'ja') else 'openai_tts'),
            'relationshipLevel': relationship_style,
            'mentalState': data['mental_state']
        }
        
        # 優先順位付きサジェスチョンを生成
        greeting_data['suggestions'] = generate_prioritized_suggestions(
            data, visitor_info, relationship_style, language
        )
        
        emit('greeting', greeting_data)
    
    emit('status', {'message': '接続成功'})
    emit('current_language', {'language': session_data[session_id]['language']})

@socketio.on('set_language')
def handle_set_language(data):
    session_id = request.sid
    language = data.get('language', 'ja')
    
    session_info = get_session_data(session_id)
    session_info['language'] = language
    
    # 関係性レベルを確認
    visitor_id = session_info.get('visitor_id')
    visitor_info = None
    relationship_style = 'formal'
    if visitor_id and visitor_id in visitor_data:
        visitor_info = visitor_data[visitor_id]
        conversation_count = visitor_info.get('total_conversations', 0)
        rel_info = calculate_relationship_level(conversation_count)
        relationship_style = rel_info['style']
    
    print(f"🌍 言語設定変更: {session_id} -> {language}")
    
    emit('language_changed', {'language': language})
    
    # 関係性レベルに応じた挨拶
    greeting_message = get_relationship_adjusted_greeting(language, relationship_style)
    greeting_emotion = "happy"
    
    try:
        audio_data = generate_audio_by_language(
            greeting_message, 
            language, 
            emotion_params=greeting_emotion
        )
    except Exception as e:
        print(f"❌ 挨拶音声生成エラー: {e}")
        audio_data = None
    
    greeting_data = {
        'message': greeting_message,
        'emotion': greeting_emotion,
        'audio': audio_data,
        'isGreeting': True,
        'language': language,
        'voice_engine': 'azure_speech' if (use_azure_speech and language == 'ja') else ('coe_font' if (use_coe_font and language == 'ja') else 'openai_tts'),
        'relationshipLevel': relationship_style,
        'mentalState': session_info['mental_state']
    }
    
    # 言語に応じたサジェスチョンを生成
    greeting_data['suggestions'] = generate_prioritized_suggestions(
        session_info, visitor_info, relationship_style, language
    )
    
    emit('greeting', greeting_data)

@socketio.on('disconnect')
def handle_disconnect():
    session_id = request.sid
    
    # セッション終了時に訪問者データを更新
    if session_id in session_data:
        session_info = session_data[session_id]
        visitor_id = session_info.get('visitor_id')
        
        if visitor_id:
            update_visitor_data(visitor_id, session_info)
        
        del session_data[session_id]
    
    print(f'🔌 クライアント切断: {session_id}')
    print_cache_stats()

# ====== 音声メッセージハンドラー ======
@socketio.on('audio_message')
def handle_audio_message(data):
    """音声入力からテキストへ変換してメッセージ処理"""
    session_id = request.sid
    
    try:
        print(f"🎤 音声メッセージ受信: Session={session_id}")
        
        # 音声データを取得
        audio_base64 = data.get('audio')
        language = data.get('language', 'ja')
        
        if not audio_base64:
            print("❌ 音声データが空です")
            emit('error', {
                'message': '音声データを受信できませんでした。' if language == 'ja' else 'Failed to receive audio data.'
            })
            return
        
        # 音声→テキスト変換
        try:
            print("🔄 音声認識開始...")
            text = speech_processor.transcribe_audio(audio_base64, language)
            
            if not text or text.strip() == "":
                print("⚠️ 音声認識結果が空です")
                emit('error', {
                    'message': '音声が認識できませんでした。もう一度お試しください。' if language == 'ja' else 'Could not recognize speech. Please try again.'
                })
                return
            
            print(f"✅ 音声認識成功: '{text}'")
            
            # 認識されたテキストをクライアントに送信（確認用）
            emit('transcription', {
                'text': text,
                'language': language
            })
            
            # テキストメッセージとして処理（既存のhandle_message()を再利用）
            message_data = {
                'message': text,
                'language': language,
                'visitorId': data.get('visitorId'),
                'conversationHistory': data.get('conversationHistory', []),
                'visitData': data.get('visitData', {}),
                'interactionCount': data.get('interactionCount', 0),
                'relationshipLevel': data.get('relationshipLevel', 'formal'),
                'selectedSuggestions': data.get('selectedSuggestions', []),
                'fromAudio': True  # 音声入力であることを示すフラグ
            }
            
            # 既存のメッセージハンドラーを呼び出し
            handle_message(message_data)
            
        except Exception as transcription_error:
            print(f"❌ 音声認識エラー: {transcription_error}")
            import traceback
            traceback.print_exc()
            
            emit('error', {
                'message': '音声認識に失敗しました。もう一度お試しください。' if language == 'ja' else 'Speech recognition failed. Please try again.'
            })
            
    except Exception as e:
        print(f"❌ 音声メッセージ処理エラー: {e}")
        import traceback
        traceback.print_exc()
        
        emit('error', {
            'message': '音声処理に失敗しました。' if data.get('language', 'ja') == 'ja' else 'Audio processing failed.'
        })

# ====== 【修正2】🧠 会話記憶対応メッセージハンドラー(感情履歴管理強化版 + suggestion即座記録) ======
@socketio.on('message')
def handle_message(data):
    global chatbot
    start_time = time.time()
    
    try:
        session_id = request.sid
        session_info = get_session_data(session_id)
        language = session_info['language']
        
        message = data.get('message', '')
        visitor_id = data.get('visitorId')
        conversation_history = data.get('conversationHistory', [])
        interaction_count = data.get('interactionCount', session_info['interaction_count'])
        selected_suggestions_from_client = data.get('selectedSuggestions', [])
        
        # インタラクション数を更新
        session_info['interaction_count'] = interaction_count + 1
        
        # 訪問者IDを更新
        if visitor_id:
            session_info['visitor_id'] = visitor_id
        
        # ✅ クライアントから送信された選択済みサジェスチョンをセッションに保存
        if selected_suggestions_from_client:
            session_info['selected_suggestions'] = list(selected_suggestions_from_client)
            print(f"📝 Selected suggestions updated from client: {len(selected_suggestions_from_client)} items")
            print(f"📊 Selected suggestions: {selected_suggestions_from_client}")
        
        # 訪問者データにも保存
        if visitor_id and visitor_id in visitor_data:
            if selected_suggestions_from_client:
                visitor_data[visitor_id]['selected_suggestions'] = set(selected_suggestions_from_client)
                print(f"👤 Visitor {visitor_id}: {len(selected_suggestions_from_client)} suggestions recorded")
        
        # 関係性レベルを計算
        visitor_info = None
        relationship_style = 'formal'
        if visitor_id and visitor_id in visitor_data:
            visitor_info = visitor_data[visitor_id]
            conversation_count = visitor_info.get('total_conversations', 0) + interaction_count
            rel_info = calculate_relationship_level(conversation_count)
            relationship_style = rel_info['style']
            session_info['relationship_style'] = relationship_style
        
        # キャッシュキーの生成(質問の正規化)
        normalized_message = normalize_question(message)
        cache_key = hashlib.md5(f"{normalized_message}_{language}".encode()).hexdigest()
        
        # キャッシュチェック
        cached_response = None
        if cache_key in conversation_cache:
            cached_data = conversation_cache[cache_key]
            # キャッシュの有効期限チェック(24時間)
            if datetime.now() - cached_data['timestamp'] < timedelta(hours=24):
                cached_response = cached_data['response']
                print(f"💾 キャッシュヒット: {cache_key[:8]}")
        
        # RAGシステムでの応答生成(キャッシュミスの場合)
        if cached_response:
            response = cached_response['message']
            emotion = cached_response['emotion']
            mental_state = cached_response.get('mental_state')
        else:
            print(f"🤖 新規応答生成: {message[:50]}...")
            
            # RAG応答生成
            if chatbot:
                # 感情分析(ユーザーメッセージから)
                user_emotion = analyze_emotion(message)
                
                # RAG応答生成
                response = chatbot.get_response(
                    message,
                    language=language,
                    conversation_history=conversation_history
                )
                
                # 応答の感情分析(改善版を使用)
                emotion = analyze_emotion(response)
                
                # 感情を検証
                emotion = validate_emotion(emotion)
                
                # 精神状態の計算
                mental_state = calculate_mental_state(session_info)
                
                # 関係性に応じた応答調整
                response = adjust_response_style(response, language, relationship_style)
                
            else:
                # chatbotが初期化されていない場合は再初期化を試行
                print("⚠️ chatbotが初期化されていません。再初期化を試みます...")
                try:
                    from modules.rag_system import RAGSystem
                    chatbot = RAGSystem()
                    print("✅ chatbot再初期化成功")
                    
                    # 再帰的に処理を実行
                    response = chatbot.get_response(
                        message,
                        language=language,
                        conversation_history=conversation_history
                    )
                    emotion = analyze_emotion(response)
                    emotion = validate_emotion(emotion)
                    mental_state = calculate_mental_state(session_info)
                    response = adjust_response_style(response, language, relationship_style)
                    
                except Exception as e:
                    print(f"❌ chatbot再初期化エラー: {e}")
                    if language == 'en':
                        response = "Sorry, the system is currently initializing. Please try again in a moment."
                    else:
                        response = "申し訳ございません。システムが初期化中です。少々お待ちください。"
                    emotion = 'neutral'
                    mental_state = session_info.get('mental_state')
            
            # キャッシュに保存
            conversation_cache[cache_key] = {
                'response': {
                    'message': response,
                    'emotion': emotion,
                    'mental_state': mental_state
                },
                'timestamp': datetime.now()
            }
        
        # 感情履歴を更新(🎯 重要)
        update_emotion_history(session_id, emotion, mental_state)
        
        # 音声生成
        try:
            audio_data = generate_audio_by_language(response, language, emotion_params=emotion)
            if audio_data:
                print(f"🔊 音声データ準備完了: {len(audio_data)} バイト")
            else:
                print("⚠️ 音声データが生成されませんでした")
        except Exception as e:
            print(f"❌ 音声生成エラー: {e}")
            audio_data = None
        
        # サジェスチョン生成
        suggestions = generate_prioritized_suggestions(
            session_info, visitor_info, relationship_style, language
        )
        
        # 処理時間計測
        processing_time = time.time() - start_time
        
        # メディアデータの取得（元の質問から独立取得）
        media_data = None
        try:
            from modules.static_qa_data import get_qa_media
            media_data = get_qa_media(message)  # 元の質問を使用
            if media_data:
                print(f"📷 メディアデータ取得: images={len(media_data.get('images', []))}, videos={len(media_data.get('videos', []))}")
        except ImportError as e:
            print(f"⚠️ メディアモジュールのインポートエラー: {e}")
        except Exception as e:
            print(f"⚠️ メディア取得エラー: {e}")
        
        # レスポンスデータの構築
        response_data = {
            'message': response,
            'emotion': emotion,
            'audio': audio_data,
            'language': language,
            'voice_engine': 'azure_speech' if (use_azure_speech and language == 'ja') else ('coe_font' if (use_coe_font and language == 'ja') else 'openai_tts'),
            'processingTime': round(processing_time, 2),
            'suggestions': suggestions,
            'relationshipLevel': relationship_style,
            'interactionCount': session_info['interaction_count'],
            'mentalState': mental_state
        }
        
        # メディアデータがある場合のみ追加（後方互換性維持）
        if media_data:
            response_data['media'] = media_data
            print(f"📤 メディアデータを含むレスポンス送信")
        
        # Socket.IOで送信
        emit('response', response_data)
        
        # 統計出力
        print(f"⏱️ 処理時間: {processing_time:.2f}秒")
        print(f"🎭 感情: {emotion}")
        print(f"💬 関係性: {relationship_style}")
        print(f"📊 インタラクション数: {session_info['interaction_count']}")
        
    except Exception as e:
        print(f"❌ メッセージ処理エラー: {e}")
        import traceback
        traceback.print_exc()
        
        emit('error', {
            'message': '申し訳ございません。エラーが発生しました。',
            'emotion': 'neutral'
        })

# ====== クイズシステム Socket.IOハンドラ ======

@socketio.on('request_quiz_proposal')
def handle_request_quiz_proposal(data):
    """クイズ提案を生成して送信"""
    session_id = request.sid
    language = data.get('language', 'ja')
    
    # 提案メッセージ（クイズ+アンケートで報酬）
    proposal_text = {
        'ja': '理解度レベルがMAXになりました！クイズとアンケートに答えてくれたら素敵なプレゼントがもらえるよ！挑戦しますか？',
        'en': 'Your understanding level is MAX! Answer the quiz and survey to get a special present! Will you try?'
    }
    
    message = proposal_text.get(language, proposal_text['ja'])
    emotion = 'happy'
    
    # 音声生成
    try:
        audio_data = generate_audio_by_language(message, language, emotion_params=emotion)
    except Exception as e:
        print(f"❌ クイズ提案音声生成エラー: {e}")
        audio_data = None
    
    emit('quiz_proposal', {
        'message': message,
        'emotion': emotion,
        'audio': audio_data
    })
    
    print(f"🎯 クイズ提案送信: Session={session_id}, Language={language}")

@socketio.on('quiz_start')
def handle_quiz_start(data):
    """クイズ開始処理"""
    session_id = request.sid
    session_info = get_session_data(session_id)
    language = data.get('language', 'ja')
    
    # クイズセッションを初期化
    quiz_sessions[session_id] = {
        'current_question': 0,
        'correct_answers': 0,
        'language': language,
        'answers': []
    }
    
    # 最初の問題を送信（遅延なし）
    send_quiz_question(session_id, language, 0)
    
    print(f"🎯 クイズ開始: Session={session_id}, Language={language}")

@socketio.on('quiz_answer')
def handle_quiz_answer(data):
    """クイズ回答処理（🎯 修正: socketio.sleep削除、クライアント側で遅延処理）"""
    session_id = request.sid
    language = data.get('language', 'ja')
    
    question_index = data.get('questionIndex')
    selected_index = data.get('selectedIndex')
    is_correct = data.get('isCorrect')
    current_question = data.get('currentQuestion')
    total_correct = data.get('totalCorrect', 0)
    
    # セッション情報を更新
    if session_id in quiz_sessions:
        quiz_sessions[session_id]['current_question'] = current_question
        quiz_sessions[session_id]['correct_answers'] = total_correct
        quiz_sessions[session_id]['answers'].append({
            'question': question_index,
            'selected': selected_index,
            'correct': is_correct
        })
    
    # 結果メッセージ生成
    question_data = QUIZ_DATA[language][question_index]
    
    if is_correct:
        result_text = {
            'ja': 'すごい！正解です！',
            'en': 'Amazing! Correct!'
        }
        emotion = 'surprise'
    else:
        result_text = {
            'ja': 'あぁ、惜しいです！',
            'en': 'Oh, so close!'
        }
        emotion = 'sad'
    
    result_message = result_text.get(language, result_text['ja'])
    explanation = question_data['explanation']
    
    # 音声生成（結果+解説）
    audio_text = f"{result_message} {explanation}"
    try:
        audio_data = generate_audio_by_language(audio_text, language, emotion_params=emotion)
    except Exception as e:
        print(f"❌ 回答結果音声生成エラー: {e}")
        audio_data = None
    
    # 🎯 修正: 次の処理タイプを判定（クライアント側で遅延処理するため）
    has_next_question = current_question < len(QUIZ_DATA[language])
    
    # 回答結果を送信（次の処理情報を含む）
    emit('quiz_answer_result', {
        'questionIndex': question_index,
        'isCorrect': is_correct,
        'correctOption': question_data['options'][question_data['correct']],
        'explanation': explanation,
        'resultMessage': result_message,
        'emotion': emotion,
        'audio': audio_data,
        'hasNextQuestion': has_next_question,
        'nextQuestionIndex': current_question if has_next_question else None,
        'isFinalResult': not has_next_question,
        'totalCorrect': total_correct
    })
    
    print(f"📝 クイズ回答: Q{question_index+1}, 正解={is_correct}, 次={'あり' if has_next_question else '最終結果'}")

@socketio.on('quiz_declined')
def handle_quiz_declined():
    """クイズ辞退処理"""
    session_id = request.sid
    session_info = get_session_data(session_id)
    language = session_info.get('language', 'ja')
    
    decline_text = {
        'ja': 'わかった！また挑戦したくなったら声をかけてね！',
        'en': 'Okay! Let me know when you want to try!'
    }
    
    message = decline_text.get(language, decline_text['ja'])
    
    # 音声生成
    try:
        audio_data = generate_audio_by_language(message, language, emotion_params='neutral')
    except Exception as e:
        print(f"❌ 辞退メッセージ音声生成エラー: {e}")
        audio_data = None
    
    emit('response', {
        'message': message,
        'emotion': 'neutral',
        'audio': audio_data,
        'language': language
    })
    
    print(f"🚫 クイズ辞退: Session={session_id}")

@socketio.on('quiz_quit')
def handle_quiz_quit():
    """クイズ中断処理"""
    session_id = request.sid
    session_info = get_session_data(session_id)
    language = session_info.get('language', 'ja')
    
    quit_text = {
        'ja': 'わかった！準備ができたらまた挑戦してね！',
        'en': 'Okay! Come back when you\'re ready!'
    }
    
    message = quit_text.get(language, quit_text['ja'])
    
    # 音声生成
    try:
        audio_data = generate_audio_by_language(message, language, emotion_params='neutral')
    except Exception as e:
        print(f"❌ 中断メッセージ音声生成エラー: {e}")
        audio_data = None
    
    emit('response', {
        'message': message,
        'emotion': 'neutral',
        'audio': audio_data,
        'language': language
    })
    
    # クイズセッションをクリア
    if session_id in quiz_sessions:
        del quiz_sessions[session_id]
    
    print(f"🚫 クイズ中断: Session={session_id}")

# 🎯 新規追加: クライアントからのリクエスト処理ハンドラ
@socketio.on('request_next_quiz_question')
def handle_request_next_quiz_question(data):
    """次の問題をリクエスト（クライアント側の遅延処理後に呼ばれる）"""
    session_id = request.sid
    language = data.get('language', 'ja')
    question_index = data.get('questionIndex', 0)
    
    # 次の問題を送信
    send_quiz_question(session_id, language, question_index)
    print(f"➡️ 次の問題送信: Q{question_index + 1}")

@socketio.on('request_quiz_final_result')
def handle_request_quiz_final_result(data):
    """最終結果をリクエスト（クライアント側の遅延処理後に呼ばれる）"""
    session_id = request.sid
    language = data.get('language', 'ja')
    total_correct = data.get('totalCorrect', 0)
    
    # 最終結果を送信
    send_quiz_final_result(session_id, language, total_correct)
    print(f"🏆 最終結果送信: Score={total_correct}/3")

@socketio.on('request_stage3_suggestions')
def handle_request_stage3_suggestions(data):
    """stage3のサジェスチョンをリクエスト（全問正解時）"""
    session_id = request.sid
    language = data.get('language', 'ja')
    
    try:
        # stage3のサジェスチョンを取得
        from modules.static_qa_data import get_suggestions_for_stage
        
        stage3_suggestions = get_suggestions_for_stage('stage3_personal', [], language)
        
        # ランダムに3つ選択
        import random
        if len(stage3_suggestions) > 3:
            selected_suggestions = random.sample(stage3_suggestions, 3)
        else:
            selected_suggestions = stage3_suggestions
        
        # クライアントに送信
        emit('stage3_suggestions', {
            'suggestions': selected_suggestions
        })
        
        print(f"📋 stage3サジェスチョン送信: {len(selected_suggestions)}個")
        
    except Exception as e:
        print(f"❌ stage3サジェスチョン取得エラー: {e}")
        emit('stage3_suggestions', {
            'suggestions': []
        })

# ヘルパー関数
def send_quiz_question(session_id, language, question_index):
    """指定された問題を送信（🎯 修正: イベント名を動的に変更）"""
    if question_index >= len(QUIZ_DATA[language]):
        return
    
    question_data = QUIZ_DATA[language][question_index]
    question_text = f"問題{question_index + 1}: {question_data['question']}" if language == 'ja' else f"Question {question_index + 1}: {question_data['question']}"
    
    # 音声生成
    try:
        audio_data = generate_audio_by_language(question_text, language, emotion_params='neutraltalking')
    except Exception as e:
        print(f"❌ 問題音声生成エラー: {e}")
        audio_data = None
    
    # 🎯 修正: イベント名を統一（クライアント側で同じハンドラが処理）
    event_name = 'next_quiz_question' if question_index > 0 else 'quiz_question'
    
    # 現在のクライアントに送信
    emit(event_name, {
        'questionIndex': question_index,
        'question': question_data['question'],
        'options': question_data['options'],
        'totalQuestions': len(QUIZ_DATA[language]),
        'correct': question_data['correct'],
        'audio': audio_data
    })

def send_quiz_final_result(session_id, language, score):
    """クイズの最終結果を送信"""
    session_info = get_session_data(session_id)
    visitor_id = session_info.get('visitor_id')
    
    all_correct = score == 3
    
    if all_correct:
        # 全問正解（🎯 修正: アンケートへの誘導メッセージ）
        result_text = {
            'ja': 'すごい！全問正解です！最後にアンケートに答えてくれたら、素敵なプレゼントをお渡しします！',
            'en': 'Amazing! All correct! Please answer a quick survey to receive your special present!'
        }
        emotion = 'happy'
        
        # 訪問者データを更新 - Masterレベルに昇格
        if visitor_id and visitor_id in visitor_data:
            visitor_data[visitor_id]['quiz_completed'] = True
            visitor_data[visitor_id]['quiz_score'] = score
            visitor_data[visitor_id]['relationship_level'] = 5  # Masterレベル
        
        session_info['quiz_completed'] = True
        session_info['quiz_score'] = score  # スコアを保存（アンケート送信時に使用）
        
    else:
        # 不正解あり
        result_text = {
            'ja': f'{score}/3問正解でした。再度挑戦しますか？',
            'en': f'You got {score}/3 correct. Try again?'
        }
        emotion = 'neutral'
    
    message = result_text.get(language, result_text['ja'])
    
    # 音声生成
    try:
        audio_data = generate_audio_by_language(message, language, emotion_params=emotion)
    except Exception as e:
        print(f"❌ 最終結果音声生成エラー: {e}")
        audio_data = None
    
    # クイズセッションをクリア
    if session_id in quiz_sessions:
        del quiz_sessions[session_id]
    
    # 現在のクライアントに送信（全問正解時は showSurvey: true を追加）
    emit('quiz_final_result', {
        'message': message,
        'emotion': emotion,
        'audio': audio_data,
        'allCorrect': all_correct,
        'showSurvey': all_correct  # 全問正解時はアンケートを表示
    })
    
    print(f"🏆 クイズ完了: Session={session_id}, Score={score}/3, ShowSurvey={all_correct}")


# ====== 📋 アンケート関連ハンドラ ======
@socketio.on('get_survey_questions')
def handle_get_survey_questions(data):
    """アンケート質問を取得"""
    language = data.get('language', 'ja')
    questions = SURVEY_QUESTIONS.get(language, SURVEY_QUESTIONS['ja'])
    emit('survey_questions', {'questions': questions})
    print(f"📋 アンケート質問送信: 言語={language}, 質問数={len(questions)}")


@socketio.on('submit_survey')
def handle_submit_survey(data):
    """アンケート回答を保存"""
    session_id = request.sid
    session_info = get_session_data(session_id)
    visitor_id = session_info.get('visitor_id')
    language = data.get('language', 'ja')
    
    # アンケートデータを構築
    survey_data = {
        'avatar_name': 'REI',
        'visitor_id': visitor_id,
        'quiz_score': session_info.get('quiz_score', 0),
        'conversation_count': session_info.get('conversation_count', 0),
        'q1': data.get('q1', ''),
        'q2': data.get('q2', ''),
        'q3': data.get('q3', ''),
        'language': language
    }
    
    # Googleスプレッドシートに保存
    success = False
    if survey_manager and survey_manager.enabled:
        success = survey_manager.save_survey(survey_data)
    else:
        print("⚠️ アンケートシステムが無効のため、ローカルログのみ")
        print(f"📋 アンケートデータ: {survey_data}")
        success = True  # ローカルログは成功扱い
    
    # 結果を送信
    emit('survey_submitted', {
        'success': success,
        'showReward': True  # アンケート完了後に報酬を表示
    })
    
    print(f"📋 アンケート提出: Session={session_id}, Success={success}")

# ====== システム初期化（モジュールロード時に実行） ======
# Gunicorn経由でも確実に実行されるように、モジュールレベルで初期化
initialize_system()

# ====== メイン実行 ======
if __name__ == '__main__':
    # サーバー起動
    port = int(os.environ.get('PORT', 5001))
    print(f"🚀 サーバー起動中... http://localhost:{port}")
    
    socketio.run(
        app, 
        debug=False,  # デバッグモード無効化(werkzeug互換性問題を回避)
        host='0.0.0.0', 
        port=port
    )