"""
多模态服务模块
提供语音识别、语音合成、摄像头表情识别等功能。
所有 import 都放在类内部延迟加载，避免环境缺少依赖时影响 app 启动。
表情识别使用 千问视觉 API（qwen-vl-max），比本地 Haar/DeepFace 更准确。
"""
import io


class SpeechRecognizer:
    def __init__(self, language='zh-CN'):
        self.language = language
        self.recognizer = None
        try:
            import speech_recognition as sr
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
        except ImportError:
            pass

    def listen(self, timeout=5.0, phrase_limit=10.0):
        if not self.recognizer:
            return ''
        import speech_recognition as sr
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
        except Exception:
            return ''
        try:
            return self.recognizer.recognize_google(audio, language=self.language)
        except Exception:
            return ''


class TextToSpeech:
    def __init__(self, engine='pyttsx3'):
        self.tts = None
        if engine == 'pyttsx3':
            try:
                import pyttsx3
                self.tts = pyttsx3.init()
                for v in self.tts.getProperty('voices'):
                    if 'zh' in v.id.lower():
                        self.tts.setProperty('voice', v.id)
                        break
                self.tts.setProperty('rate', 160)
                self.tts.setProperty('volume', 0.9)
            except ImportError:
                pass

    def speak(self, text):
        if text and self.tts:
            self.tts.say(text)
            self.tts.runAndWait()


class EmotionDetector:
    """
    摄像头表情识别器
    使用 千问视觉 API（qwen-vl-max）分析每一帧的人脸表情。
    本地只负责摄像头画面捕获和帧率控制。
    """

    EMOTION_CN_MAP = {
        'happy': '😊 开心', 'sad': '😢 悲伤', 'angry': '😠 生气',
        'surprise': '😮 惊讶', 'fear': '😨 恐惧', 'disgust': '🤢 厌恶',
        'neutral': '😐 平静', 'contempt': '😏 轻蔑'
    }

    def __init__(self, camera_id=0, interval=3.0):
        """
        Args:
            camera_id: int, 摄像头编号
            interval: float, 两次 API 分析之间的最小间隔（秒），避免频繁调用浪费额度
        """
        self.camera_id = camera_id
        self.interval = interval
        self.camera = None
        self.running = False
        self.current_emotion = 'neutral'
        self.current_emotion_cn = '😐 平静'
        self._emotion_vector = {
            'valence': 0.5, 'arousal': 0.5, 'dominance': 0.5,
            'anxiety': 0.0, 'fatigue': 0.0, 'engagement': 0.5,
        }
        self.last_detect_time = 0
        self.frame = None
        self._lock = None
        self._cv2_available = False
        self._init_imports()

    def _init_imports(self):
        try:
            import cv2
            self._cv2_available = True
            self._lock = __import__('threading').Lock()
        except ImportError:
            pass

    def start(self):
        if not self._cv2_available:
            return False
        import cv2
        try:
            self.camera = cv2.VideoCapture(self.camera_id)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            if not self.camera.isOpened():
                return False
            self.running = True
            import threading
            t = threading.Thread(target=self._capture_loop, daemon=True)
            t.start()
            return True
        except Exception:
            return False

    def stop(self):
        self.running = False
        if self.camera:
            import cv2
            self.camera.release()
            self.camera = None

    def _capture_loop(self):
        """
        摄像头捕获循环：
        - 持续读取帧，保存最新一帧
        - 按 interval 间隔调用千问 API 分析表情
        """
        import cv2
        import time

        while self.running:
            ret, frame = self.camera.read()
            if not ret:
                time.sleep(0.1)
                continue
            with self._lock:
                self.frame = frame.copy()

            now = time.time()
            if now - self.last_detect_time >= self.interval:
                self.last_detect_time = now
                self._analyze_emotion(frame)

            time.sleep(0.03)

    def _analyze_emotion(self, frame):
        """
        将帧编码为 JPEG → 调用千问 API 进行维度情绪分析
        不仅输出离散情绪标签，还输出 VAD + 焦虑/疲劳/参与度 连续量表值
        """
        import cv2
        try:
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
            image_bytes = io.BytesIO(buffer.tobytes()).getvalue()

            from services.ai_service import analyze_facial_expression
            result = analyze_facial_expression(image_bytes)

            self.current_emotion = result.get("emotion", "neutral")
            emoji_cn = self.EMOTION_CN_MAP.get(self.current_emotion, '😐 平静')
            analysis = result.get("analysis", "")

            # 构建显示文本（包含维度值）
            parts = [emoji_cn]
            if analysis:
                parts.append(analysis)

            # 生成情绪维度详情（供后续评分系统使用）
            self._emotion_vector = {
                "valence": result.get("valence", 0.5),
                "arousal": result.get("arousal", 0.5),
                "dominance": result.get("dominance", 0.5),
                "anxiety": result.get("anxiety", 0.0),
                "fatigue": result.get("fatigue", 0.0),
                "engagement": result.get("engagement", 0.5),
            }

            self.current_emotion_cn = " | ".join(parts)

        except Exception:
            pass

    def get_emotion(self):
        return {
            'emotion': self.current_emotion,
            'emotion_cn': self.current_emotion_cn,
            'vector': getattr(self, '_emotion_vector', {
                'valence': 0.5, 'arousal': 0.5, 'dominance': 0.5,
                'anxiety': 0.0, 'fatigue': 0.0, 'engagement': 0.5,
            }),
        }

    def get_frame(self):
        if self._lock is None:
            return None
        with self._lock:
            return self.frame.copy() if self.frame is not None else None


class MultimodalManager:
    def __init__(self):
        self.speech = SpeechRecognizer()
        self.tts = TextToSpeech()
        self.emotion = EmotionDetector()
        self.emotion_started = False

    def start_emotion_detection(self):
        if not self.emotion_started:
            self.emotion_started = self.emotion.start()
        return self.emotion_started

    def stop_emotion_detection(self):
        self.emotion.stop()
        self.emotion_started = False

    def listen_speech(self, timeout=5.0):
        return self.speech.listen(timeout=timeout)

    def speak_text(self, text):
        self.tts.speak(text)

    def get_current_emotion(self):
        return self.emotion.get_emotion()

    def get_emotion_frame(self):
        return self.emotion.get_frame()

    def cleanup(self):
        self.stop_emotion_detection()
