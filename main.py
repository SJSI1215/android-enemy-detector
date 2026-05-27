"""
安卓AI实时敌人检测 APK
Kivy + OpenCV + Android MediaProjection
"""
import os, time, numpy as np, cv2
from collections import deque
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.togglebutton import ToggleButton
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.window import Window


class EnemyDetector:
    """移动敌人检测 (背景差分 + 轮廓分析)"""
    def __init__(self):
        self._bg = cv2.createBackgroundSubtractorMOG2(200, 40, False)
        self._trails = {}
        self._next_id = 0

    def detect(self, frame):
        h, w = frame.shape[:2]
        display = frame.copy()
        fg = self._bg.apply(frame)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, kernel, iterations=2)
        contours, _ = cv2.findContours(fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        count = 0
        cur_ids = set()
        for c in contours:
            area = cv2.contourArea(c)
            if area < 200 or area > 60000: continue
            x, y, bw, bh = cv2.boundingRect(c)
            aspect = bh / max(bw, 1)
            if aspect < 0.7 or aspect > 4.5: continue
            if x < 10 or y < 10 or x + bw > w - 10 or y + bh > h - 10: continue

            # 追踪
            cx, cy = x + bw // 2, y + bh // 2
            matched = None
            for tid, trail in self._trails.items():
                if trail:
                    lx, ly, lw, lh = trail[-1]
                    if abs(cx - (lx + lw // 2)) + abs(cy - (ly + lh // 2)) < 60:
                        matched = tid; break
            if matched is None:
                matched = self._next_id; self._next_id += 1
            self._trails.setdefault(matched, deque(maxlen=20)).append((x, y, bw, bh))
            cur_ids.add(matched)

            # 绿框
            cv2.rectangle(display, (x, y), (x + bw, y + bh), (0, 255, 0), 2)
            cv2.putText(display, f"E{matched}", (x, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            count += 1

        stale = set(self._trails) - cur_ids
        for s in stale: del self._trails[s]
        return display, count

    def reset(self):
        self._bg = cv2.createBackgroundSubtractorMOG2(200, 40, False)
        self._trails.clear()


class ScreenCapture:
    """Android MediaProjection 屏幕捕获"""
    def __init__(self):
        self._service = None
        self._init_android()

    def _init_android(self):
        try:
            from jnius import autoclass
            self._Intent = autoclass('android.content.Intent')
            self._MediaProjectionManager = autoclass(
                'android.media.projection.MediaProjectionManager'
            )
            self._ctx = autoclass('org.kivy.android.PythonActivity').mActivity
            self._available = True
        except Exception:
            self._available = False

    @property
    def available(self): return self._available

    def start(self):
        if not self._available: return False
        try:
            intent = self._Intent(self._ctx, self._MediaProjectionManager)
            self._ctx.startActivityForResult(intent, 1001)
            return True
        except: return False

    def capture(self):
        """从当前窗口截帧 (回退方案: 读screenshot)"""
        try:
            import subprocess
            r = subprocess.run(["screencap", "-p"], capture_output=True, timeout=3)
            if r.returncode == 0:
                arr = np.frombuffer(r.stdout, np.uint8)
                return cv2.imdecode(arr, cv2.IMREAD_COLOR)
        except: pass

        # 最低回退: 读文件
        try:
            return cv2.imread("/sdcard/screen.png")
        except: return None


class AndroidDetectorApp(App):
    def build(self):
        self._detector = EnemyDetector()
        self._capture = ScreenCapture()
        self._running = False

        layout = BoxLayout(orientation='vertical', padding=10, spacing=5)

        # 状态标签
        self._status = Label(text="就绪 | 点击开始检测", size_hint=(1, 0.05),
                              color=(0.5, 1, 0.5, 1))
        layout.add_widget(self._status)

        # 预览
        self._preview = Image(size_hint=(1, 0.85))
        layout.add_widget(self._preview)

        # 按钮栏
        btn_layout = BoxLayout(size_hint=(1, 0.08), spacing=5)

        self._toggle = ToggleButton(text="开始检测")
        self._toggle.bind(on_press=self._on_toggle)
        btn_layout.add_widget(self._toggle)

        reset_btn = Button(text="重置")
        reset_btn.bind(on_press=lambda x: self._detector.reset())
        btn_layout.add_widget(reset_btn)

        layout.add_widget(btn_layout)

        # 计数
        self._count = Label(text="目标: 0 | FPS: --", size_hint=(1, 0.03),
                             color=(0.7, 0.7, 0.7, 1))
        layout.add_widget(self._count)

        # 帧率统计
        self._fps_times = deque(maxlen=30)
        self._frame_idx = 0  # 避免截图过多

        return layout

    def _on_toggle(self, btn):
        if btn.state == 'down':
            self._running = True
            self._status.text = "检测中..."
            self._status.color = (0, 1, 0, 1)
            Clock.schedule_interval(self._update, 1.0 / 20.0)  # 20fps
        else:
            self._running = False
            self._status.text = "已停止"
            self._status.color = (0.5, 0.5, 0.5, 1)
            Clock.unschedule(self._update)

    def _update(self, dt):
        if not self._running: return
        t0 = time.time()

        # 截帧 (每3帧截一次以降低开销)
        self._frame_idx += 1
        if self._frame_idx % 3 == 0:
            frame = self._capture.capture()
            if frame is not None:
                self._last_frame = frame
            else:
                return
        else:
            frame = getattr(self, '_last_frame', None)
            if frame is None: return

        # 检测
        display, count = self._detector.detect(frame)
        self._count.text = f"目标: {count}"

        # 显示
        h, w = display.shape[:2]
        rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
        # 缩放
        scale = min(Window.width / w, Window.height * 0.85 / h, 1.0)
        if scale < 1.0:
            rgb = cv2.resize(rgb, (int(w * scale), int(h * scale)))
        rgb_flip = cv2.flip(rgb, 0)
        buf = rgb_flip.tobytes()

        tex = Texture.create(size=(rgb_flip.shape[1], rgb_flip.shape[0]), colorfmt='rgb')
        tex.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
        self._preview.texture = tex

        # FPS
        self._fps_times.append(time.time() - t0)
        if self._fps_times:
            fps = len(self._fps_times) / sum(self._fps_times)
            self._count.text = f"目标: {count} | FPS: {fps:.0f}"


if __name__ == '__main__':
    AndroidDetectorApp().run()
