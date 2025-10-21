import threading
import io
import os
import re
import json
import random
import string
import traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from urllib.parse import urljoin

# Optional Pillow import for background images
try:
    from PIL import Image, ImageTk  # type: ignore
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False
    Image = None  # type: ignore
    ImageTk = None  # type: ignore


class CaptchaApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Audio Captcha Helper")
        self.root.geometry("980x640")
        self.root.minsize(800, 520)

        # State
        self.worker_thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.bg_pil_image = None  # type: ignore[assignment]
        self.bg_tk_image = None

        # Layers: background canvas + overlay UI
        self.background_canvas = tk.Canvas(self.root, highlightthickness=0, bd=0)
        self.background_canvas.pack(fill=tk.BOTH, expand=True)

        self.overlay = tk.Frame(self.root, bg="", highlightthickness=0)
        self.overlay.place(relx=0.5, rely=0.5, anchor="center")

        self._build_controls(self.overlay)

        # Logging panel attached to root, sits on top of canvas at bottom
        self.log_frame = ttk.Frame(self.root)
        self.log_frame.place(relx=0.5, rely=0.98, anchor="s", relwidth=0.92, relheight=0.36)
        self._build_log(self.log_frame)

        # Redraw on resize
        self.root.bind("<Configure>", self._on_resize)
        self._draw_background()

        # Close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_controls(self, parent: tk.Widget) -> None:
        card = ttk.Frame(parent)
        card.grid_columnconfigure(1, weight=1)

        title = ttk.Label(card, text="Audio Captcha Helper", font=("Segoe UI", 18, "bold"))
        subtitle = ttk.Label(card, text="Thêm background UI + chạy quy trình captcha", font=("Segoe UI", 10))

        site_label = ttk.Label(card, text="Trang:")
        self.site_var = tk.StringVar(value="mmoocode.shop")
        site_combo = ttk.Combobox(
            card,
            textvariable=self.site_var,
            values=["mmoocode.shop", "go99code.store"],
            state="readonly",
            width=18,
        )

        username_label = ttk.Label(card, text="Tên tài khoản:")
        self.username_var = tk.StringVar(value="quancaidu")
        username_entry = ttk.Entry(card, textvariable=self.username_var, width=30)

        lang_label = ttk.Label(card, text="Ngôn ngữ nhận dạng:")
        self.lang_var = tk.StringVar(value="vi-VN")
        lang_combo = ttk.Combobox(card, textvariable=self.lang_var, values=[
            "vi-VN", "en-US", "en-GB", "th-TH", "id-ID"
        ], state="readonly", width=12)

        promo_label = ttk.Label(card, text="Mã khuyến mãi:")
        self.promo_var = tk.StringVar(value="TAIAPP")
        promo_entry = ttk.Entry(card, textvariable=self.promo_var, width=20)

        bg_btn = ttk.Button(card, text="Chọn ảnh nền…", command=self._select_bg_image)
        self.start_btn = ttk.Button(card, text="Bắt đầu", command=self._start)
        self.stop_btn = ttk.Button(card, text="Dừng", command=self._stop, state=tk.DISABLED)

        # Layout
        title.grid(row=0, column=0, columnspan=3, sticky="w")
        subtitle.grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 12))

        site_label.grid(row=2, column=0, sticky="w", padx=(0, 8))
        site_combo.grid(row=2, column=1, sticky="w", pady=4)

        username_label.grid(row=3, column=0, sticky="w", padx=(0, 8))
        username_entry.grid(row=3, column=1, sticky="ew", pady=4)

        lang_label.grid(row=4, column=0, sticky="w", padx=(0, 8))
        lang_combo.grid(row=4, column=1, sticky="w", pady=4)

        promo_label.grid(row=5, column=0, sticky="w", padx=(0, 8))
        promo_entry.grid(row=5, column=1, sticky="w", pady=4)

        bg_btn.grid(row=6, column=0, sticky="w", pady=(12, 0))
        self.start_btn.grid(row=6, column=1, sticky="w", padx=(8, 0), pady=(12, 0))
        self.stop_btn.grid(row=6, column=2, sticky="w", padx=(8, 0), pady=(12, 0))

        # A little padding
        for child in card.winfo_children():
            if isinstance(child, ttk.Entry) or isinstance(child, ttk.Combobox):
                child.configure()
        card.configure(padding=16)
        card.pack(fill=tk.X)

    def _build_log(self, parent: tk.Widget) -> None:
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        label = ttk.Label(parent, text="Nhật ký hoạt động")
        label.grid(row=0, column=0, sticky="w")

        self.log_text = tk.Text(parent, height=12, wrap=tk.WORD, state=tk.DISABLED, font=("Consolas", 10))
        yscroll = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=yscroll.set)

        self.log_text.grid(row=1, column=0, sticky="nsew")
        yscroll.grid(row=1, column=1, sticky="ns")

    # Background drawing
    def _on_resize(self, event: tk.Event) -> None:  # type: ignore[override]
        if event.widget is self.root:
            self._draw_background()

    def _draw_background(self) -> None:
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        if w <= 1 or h <= 1:
            return

        self.background_canvas.delete("all")
        self.background_canvas.configure(width=w, height=h)

        if self.bg_pil_image is not None and PIL_AVAILABLE:
            # Scale the image to cover the window (maintain aspect ratio)
            img_w, img_h = self.bg_pil_image.size
            if img_w == 0 or img_h == 0:
                return
            scale = max(w / img_w, h / img_h)
            new_w = max(1, int(img_w * scale))
            new_h = max(1, int(img_h * scale))
            resized = self.bg_pil_image.resize((new_w, new_h), Image.LANCZOS)
            self.bg_tk_image = ImageTk.PhotoImage(resized)
            # Centered image
            x = (w - new_w) // 2
            y = (h - new_h) // 2
            self.background_canvas.create_image(x, y, anchor="nw", image=self.bg_tk_image)
        else:
            # Gradient fallback (blue -> purple)
            steps = 64
            for i in range(steps):
                r = int(40 + (110 - 40) * (i / steps))
                g = int(70 + (40 - 70) * (i / steps))
                b = int(180 + (200 - 180) * (i / steps))
                color = f"#{r:02x}{g:02x}{b:02x}"
                y0 = int(h * i / steps)
                y1 = int(h * (i + 1) / steps)
                self.background_canvas.create_rectangle(0, y0, w, y1, outline="", fill=color)

        # So overlay remains centered after resize
        self.overlay.lift()
        self.log_frame.lift()

    def _select_bg_image(self) -> None:
        if not PIL_AVAILABLE:
            messagebox.showwarning(
                "Thiếu phụ thuộc",
                "Pillow (PIL) chưa được cài đặt. Hãy cài đặt bằng: pip install pillow",
            )
            return
        filetypes = [
            ("Image files", "*.png *.jpg *.jpeg *.webp *.gif"),
            ("All files", "*.*"),
        ]
        path = filedialog.askopenfilename(title="Chọn ảnh nền", filetypes=filetypes)
        if not path:
            return
        try:
            img = Image.open(path).convert("RGB")
            self.bg_pil_image = img
            self._draw_background()
            self._log(f"Đã đặt ảnh nền: {os.path.basename(path)}")
        except Exception as exc:
            messagebox.showerror("Lỗi ảnh nền", f"Không thể mở ảnh: {exc}")

    # Logging utilities (thread-safe)
    def _log(self, message: str) -> None:
        self.root.after(0, self._append_log, message)

    def _append_log(self, message: str) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    # Controls
    def _start(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            return
        username = self.username_var.get().strip()
        if not username:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập tên tài khoản.")
            return
        self.stop_event.clear()
        self.start_btn.configure(state=tk.DISABLED)
        self.stop_btn.configure(state=tk.NORMAL)
        self._log("Bắt đầu quy trình…")
        self.worker_thread = threading.Thread(target=self._run_flow, name="captcha-flow", daemon=True)
        self.worker_thread.start()

    def _stop(self) -> None:
        if self.worker_thread and self.worker_thread.is_alive():
            self.stop_event.set()
            self._log("Đang dừng…")
        self.stop_btn.configure(state=tk.DISABLED)

    def _run_flow(self) -> None:
        """Run the captcha workflow in a background thread."""
        username = self.username_var.get().strip()
        lang = self.lang_var.get().strip() or "vi-VN"
        domain = (self.site_var.get().strip() or "mmoocode.shop").replace("https://", "").replace("http://", "").strip("/")
        base_url = f"https://{domain}"
        promo_code = self.promo_var.get().strip() or "TAIAPP"

        # Lazy import heavy/external deps inside thread
        try:
            import requests  # type: ignore
            import numpy as np  # type: ignore
            import librosa  # type: ignore
            import soundfile as sf  # type: ignore
            import speech_recognition as sr  # type: ignore
        except Exception as exc:
            self._log("Thiếu thư viện: hãy cài đặt: pip install requests librosa soundfile SpeechRecognition numpy pillow")
            self._log(str(exc))
            self._finalize_buttons()
            return

        def check_stop() -> bool:
            if self.stop_event.is_set():
                self._log("Đã hủy theo yêu cầu.")
                return True
            return False

        def speech_to_text_from_url(url: str, speech_lang: str = "vi-VN", session=None) -> str | None:
            """Download audio from URL, extend tail, save to temp .wav, use Google Recognizer."""
            temp_name = "".join(random.choices(string.ascii_lowercase + string.digits, k=8)) + ".wav"
            try:
                get_fn = (session.get if session is not None else requests.get)  # type: ignore[attr-defined]
                audio_bytes = get_fn(url, timeout=20).content
                y, sr_rate = librosa.load(io.BytesIO(audio_bytes), sr=16000, mono=True)
                # pad 1.3s of silence at end to avoid truncation
                y = np.concatenate([y, np.zeros(int(1.3 * sr_rate))])
                sf.write(temp_name, y, sr_rate)
                recognizer = sr.Recognizer()
                with sr.AudioFile(temp_name) as src:
                    text = recognizer.recognize_google(recognizer.record(src), language=speech_lang)
                digits = re.sub(r"\D", "", text)
                return digits or None
            except Exception as exc2:
                self._log(f"Lỗi STT: {exc2}")
                return None
            finally:
                try:
                    if os.path.exists(temp_name):
                        os.remove(temp_name)
                except Exception:
                    pass

        try:
            if check_stop():
                self._finalize_buttons()
                return

            # Prepare session
            client = requests.Session()
            client.headers.update({
                'Host': domain,
                'sec-ch-ua-platform': '"Windows"',
                'x-requested-with': 'XMLHttpRequest',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'sec-ch-ua-mobile': '?0',
                'origin': base_url,
                'sec-fetch-site': 'same-origin',
                'sec-fetch-mode': 'cors',
                'sec-fetch-dest': 'empty',
                'referer': base_url + '/',
                'accept-language': 'vi',
                'priority': 'u=1, i',
            })

            # 1) Get nonce values from homepage
            self._log("Đang lấy nonce…")
            home_html = client.get(base_url + '/', timeout=25).text

            def extract_nonces(html: str) -> tuple[str | None, str | None]:
                # Pattern 1: specific "ajax.php'; const nonce='XXXX'"
                m1 = re.findall(r"ajax\\.php'\s*;\s*const\s+nonce='([A-Za-z0-9]+)'", html)
                # Pattern 2: general const nonce='XXXX'
                m_all = re.findall(r"const\s+nonce='([A-Za-z0-9]+)'", html)
                nonce_first = m1[0] if m1 else (m_all[0] if m_all else None)
                nonce_second = None
                if m_all:
                    # Pick the first different value if available; else reuse
                    for val in m_all:
                        if val != nonce_first:
                            nonce_second = val
                            break
                if nonce_second is None:
                    nonce_second = nonce_first
                return nonce_first, nonce_second

            nonce1, nonce2 = extract_nonces(home_html)
            if not nonce1 or not nonce2:
                self._log("Không trích xuất được nonce. Có thể giao diện trang đã thay đổi.")
                self._finalize_buttons()
                return

            self._log(f"nonce1={nonce1}")
            self._log(f"nonce2={nonce2}")

            if check_stop():
                self._finalize_buttons()
                return

            # 2) Call taiApp
            self._log("Gọi get_promo_verification_type…")
            ta = client.post(
                f'{base_url}/wp-admin/admin-ajax.php',
                data={
                    'action': 'get_promo_verification_type',
                    'ma_khuyen_mai': promo_code,
                    'nonce': nonce1,
                },
                timeout=20,
            ).text
            self._log(f"KQ taiApp: {ta}")

            if check_stop():
                self._finalize_buttons()
                return

            # 3) Request audio captcha URL
            self._log("Yêu cầu audio captcha…")
            payload = {
                'action': 'generate_audio_captcha',
                'nonce': nonce2,
                'form_data': json.dumps({
                    "ten_tai_khoan": username,
                    "ma_khuyen_mai": promo_code,
                    "captcha": ""
                })
            }
            response = client.post(f'{base_url}/wp-admin/admin-ajax.php', data=payload, timeout=20)
            audio_url = None
            try:
                res_json = response.json()
                if res_json.get("success") and "data" in res_json and "audio_url" in res_json["data"]:
                    audio_url = res_json["data"]["audio_url"].replace("\\/", "/")
            except Exception:
                pass

            if not audio_url:
                self._log("Không nhận được audio_url từ server.")
                self._finalize_buttons()
                return

            # Normalize audio URL to absolute
            if not audio_url.startswith("http://") and not audio_url.startswith("https://"):
                audio_url = urljoin(base_url + '/', audio_url.lstrip('/'))
            self._log(f"audio_url: {audio_url}")

            if check_stop():
                self._finalize_buttons()
                return

            # 4) STT to digits
            self._log("Đang nhận dạng giọng nói…")
            code = speech_to_text_from_url(audio_url, speech_lang=lang, session=client)
            self._log(f"Mã nhận dạng: {code}")
            if not code:
                self._log("Không nhận dạng được mã captcha.")
                self._finalize_buttons()
                return

            if check_stop():
                self._finalize_buttons()
                return

            # 5) Verify audio captcha
            self._log("Xác minh mã captcha…")
            verify_res = client.post(
                f'{base_url}/wp-admin/admin-ajax.php',
                data={
                    'action': 'verify_audio_captcha',
                    'nonce': nonce2,
                    'captcha_input': code,
                },
                timeout=20,
            ).text
            self._log(f"KQ verify: {verify_res}")

            if check_stop():
                self._finalize_buttons()
                return

            # 6) Final form submit
            self._log("Gửi form cuối…")
            final_res = client.post(
                base_url + '/',
                data={
                    'ten_tai_khoan': username,
                    'ma_khuyen_mai': promo_code,
                    'captcha': '',
                },
                timeout=20,
            ).text
            try:
                final_msg = final_res.split("showFormError")[1].split(";")[0]
            except Exception:
                final_msg = final_res[:300] + ("…" if len(final_res) > 300 else "")
            self._log(f"KQ cuối: {final_msg}")

        except Exception as e:
            self._log("Đã xảy ra lỗi không mong muốn.")
            self._log(str(e))
            tb = traceback.format_exc(limit=1)
            self._log(tb)
        finally:
            self._finalize_buttons()

    def _finalize_buttons(self) -> None:
        def _reset():
            self.start_btn.configure(state=tk.NORMAL)
            self.stop_btn.configure(state=tk.DISABLED)
        self.root.after(0, _reset)

    def _on_close(self) -> None:
        try:
            if self.worker_thread and self.worker_thread.is_alive():
                self.stop_event.set()
                self.worker_thread.join(timeout=3)
        finally:
            self.root.destroy()


def main() -> None:
    root = tk.Tk()
    # Use ttk themes
    try:
        style = ttk.Style(root)
        # Prefer a modern theme if available
        for theme in ("vista", "clam", "alt", "default"):
            if theme in style.theme_names():
                style.theme_use(theme)
                break
    except Exception:
        pass

    app = CaptchaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
