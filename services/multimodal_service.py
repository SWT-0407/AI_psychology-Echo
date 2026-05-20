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
    摄像头表情识别器（增强版）
    使用 千问视觉 API（qwen-vl-max）分析每一帧的人脸表情。
    优化点：
    - 摄像头分辨率提升至 1280x720
    - JPEG 质量提升至 90%（减少压缩失真）
    - 自动裁切人脸区域后发送（让 AI 专注于面部）
    - 千问 API 使用 detail: "high" 模式
    - 失败时自动重试 1 次
    """

    EMOTION_CN_MAP = {
        'happy': '😊 开心', 'sad': '😢 悲伤', 'angry': '😠 生气',
        'surprise': '😮 惊讶', 'fear': '😨 恐惧', 'disgust': '🤢 厌恶',
        'neutral': '😐 平静', 'contempt': '😏 轻蔑', 'anxious': '😰 焦虑',
        'tired': '😴 疲惫'
    }

    def __init__(self, camera_id=0, interval=3.0):
        """
        Args:
            camera_id: int, 摄像头编号
            interval: float, 两次 API 分析之间的最小间隔（秒）
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
            # 提高分辨率以获得更多面部细节
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            # 尝试自动对焦
            self.camera.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            # 尝试调整亮度/对比度
            self.camera.set(cv2.CAP_PROP_BRIGHTNESS, 128)
            self.camera.set(cv2.CAP_PROP_CONTRAST, 128)
            if not self.camera.isOpened():
                return False
            # 给摄像头一点时间稳定画面
            import time
            time.sleep(0.5)
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
        - 先用 OpenCV Haar Cascade 检测人脸区域，裁切后发送给千问 API
        - 按 interval 间隔调用
        """
        import cv2
        import time

        # 加载人脸检测器
        face_cascade = None
        try:
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            face_cascade = cv2.CascadeClassifier(cascade_path)
        except Exception:
            pass

        while self.running:
            ret, frame = self.camera.read()
            if not ret:
                time.sleep(0.1)
                continue

            # 保存原帧用于显示
            with self._lock:
                self.frame = frame.copy()

            now = time.time()
            if now - self.last_detect_time >= self.interval:
                self.last_detect_time = now

                # 尝试裁切人脸区域（仅发送人脸给 API，减少干扰）
                face_img = frame
                if face_cascade is not None:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(
                        gray, scaleFactor=1.1, minNeighbors=5, minSize=(100, 100)
                    )
                    if len(faces) > 0:
                        # 取最大的人脸
                        (x, y, w, h) = max(faces, key=lambda f: f[2] * f[3])
                        # 适当扩大裁切范围（上下左右各扩 20%）
                        pad_x = int(w * 0.2)
                        pad_y = int(h * 0.2)
                        x1 = max(0, x - pad_x)
                        y1 = max(0, y - pad_y)
                        x2 = min(frame.shape[1], x + w + pad_x)
                        y2 = min(frame.shape[0], y + h + pad_y)
                        face_img = frame[y1:y2, x1:x2]

                # 分析表情
                self._analyze_emotion(face_img)

            time.sleep(0.03)

    def _analyze_emotion(self, frame):
        """
        将帧编码为高质量 JPEG → 调用千问 API（high detail）分析
        """
        import cv2
        try:
            # 高质量 JPEG 编码
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
            image_bytes = io.BytesIO(buffer.tobytes()).getvalue()

            from services.ai_service import analyze_facial_expression
            # 尝试分析，如果失败则重试一次
            result = None
            for attempt in range(2):
                result = analyze_facial_expression(image_bytes, detail="high")
                if result.get("emotion") != "neutral" or attempt == 1:
                    break

            if result is None:
                return

            self.current_emotion = result.get("emotion", "neutral")
            emoji_cn = self.EMOTION_CN_MAP.get(self.current_emotion, '😐 平静')
            analysis = result.get("analysis", "")

            # 构建显示文本
            parts = [emoji_cn]
            if analysis:
                parts.append(analysis)

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
