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
from urllib.parse import urljoin, urlparse

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
        self.root.geometry("720x520")
        self.root.minsize(680, 480)
        self.root.configure(bg="#f0f2f5")

        # State
        self.worker_thread: threading.Thread | None = None
        self.stop_event = threading.Event()
        self.bg_pil_image = None  # type: ignore[assignment]
        self.bg_tk_image = None

        # Main container with padding
        self.main_container = tk.Frame(self.root, bg="#f0f2f5")
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Control panel with modern card design
        self.control_frame = tk.Frame(self.main_container, bg="white", relief="flat", bd=0)
        self.control_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Add subtle shadow effect
        self.shadow_frame = tk.Frame(self.main_container, bg="#e0e0e0", height=2)
        self.shadow_frame.pack(fill=tk.X, pady=(0, 13))
        
        self._build_controls(self.control_frame)

        # Logging panel with modern design
        self.log_frame = tk.Frame(self.main_container, bg="white", relief="flat", bd=0)
        self.log_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add shadow for log panel
        self.log_shadow = tk.Frame(self.main_container, bg="#e0e0e0", height=2)
        self.log_shadow.pack(fill=tk.X, pady=(0, 13))
        
        self._build_log(self.log_frame)

        # Close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_controls(self, parent: tk.Widget) -> None:
        # Header section
        header_frame = tk.Frame(parent, bg="white")
        header_frame.pack(fill=tk.X, padx=20, pady=(20, 15))
        
        title = tk.Label(header_frame, text="Audio Captcha Helper", 
                        font=("Segoe UI", 20, "bold"), 
                        fg="#2c3e50", bg="white")
        title.pack(anchor="w")
        
        subtitle = tk.Label(header_frame, text="Tự động hóa quy trình captcha audio", 
                           font=("Segoe UI", 11), 
                           fg="#7f8c8d", bg="white")
        subtitle.pack(anchor="w", pady=(2, 0))

        # Main form with grid layout
        form_frame = tk.Frame(parent, bg="white")
        form_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        form_frame.grid_columnconfigure(1, weight=1)

        # Row 1: Site selection
        site_label = tk.Label(form_frame, text="Trang web:", 
                             font=("Segoe UI", 10, "bold"), 
                             fg="#34495e", bg="white")
        site_label.grid(row=0, column=0, sticky="w", padx=(0, 15), pady=(0, 8))
        
        self.site_var = tk.StringVar(value="mmoocode.shop")
        site_combo = ttk.Combobox(
            form_frame,
            textvariable=self.site_var,
            values=[
                "mmoocode.shop",
                "go99code.store", 
                "tt88code.win",
                "nohucode.shop",
                "789pcode.store",
                "link1.789pcode.win",
            ],
            state="readonly",
            width=25,
            font=("Segoe UI", 10)
        )
        site_combo.grid(row=0, column=1, sticky="ew", pady=(0, 8))

        # Row 2: Username
        username_label = tk.Label(form_frame, text="Tên tài khoản:", 
                                 font=("Segoe UI", 10, "bold"), 
                                 fg="#34495e", bg="white")
        username_label.grid(row=1, column=0, sticky="w", padx=(0, 15), pady=(0, 8))
        
        self.username_var = tk.StringVar(value="quancaidu")
        username_entry = ttk.Entry(form_frame, textvariable=self.username_var, 
                                  width=30, font=("Segoe UI", 10))
        username_entry.grid(row=1, column=1, sticky="ew", pady=(0, 8))

        # Row 3: Language and Promo code
        lang_label = tk.Label(form_frame, text="Ngôn ngữ:", 
                             font=("Segoe UI", 10, "bold"), 
                             fg="#34495e", bg="white")
        lang_label.grid(row=2, column=0, sticky="w", padx=(0, 15), pady=(0, 8))
        
        self.lang_var = tk.StringVar(value="vi-VN")
        lang_combo = ttk.Combobox(form_frame, textvariable=self.lang_var, 
                                 values=["vi-VN", "en-US", "en-GB", "th-TH", "id-ID"],
                                 state="readonly", width=15, font=("Segoe UI", 10))
        lang_combo.grid(row=2, column=1, sticky="w", pady=(0, 8))

        promo_label = tk.Label(form_frame, text="Mã khuyến mãi:", 
                              font=("Segoe UI", 10, "bold"), 
                              fg="#34495e", bg="white")
        promo_label.grid(row=3, column=0, sticky="w", padx=(0, 15), pady=(0, 8))
        
        self.promo_var = tk.StringVar(value="TAIAPP")
        promo_entry = ttk.Entry(form_frame, textvariable=self.promo_var, 
                               width=20, font=("Segoe UI", 10))
        promo_entry.grid(row=3, column=1, sticky="w", pady=(0, 8))

        # Row 4: Proxy
        proxy_label = tk.Label(form_frame, text="Proxy (tùy chọn):", 
                              font=("Segoe UI", 10, "bold"), 
                              fg="#34495e", bg="white")
        proxy_label.grid(row=4, column=0, sticky="w", padx=(0, 15), pady=(0, 8))
        
        self.proxy_var = tk.StringVar(value="")
        proxy_entry = ttk.Entry(form_frame, textvariable=self.proxy_var, 
                               width=40, font=("Segoe UI", 10))
        proxy_entry.grid(row=4, column=1, sticky="ew", pady=(0, 8))

        # Row 5: Options and buttons
        options_frame = tk.Frame(form_frame, bg="white")
        options_frame.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        self.run_both_var = tk.BooleanVar(value=False)
        run_both_chk = ttk.Checkbutton(options_frame, text="Chạy tất cả trang", 
                                       variable=self.run_both_var)
        run_both_chk.pack(side=tk.LEFT)

        # Button frame
        button_frame = tk.Frame(form_frame, bg="white")
        button_frame.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(15, 0))
        
        # Style buttons
        style = ttk.Style()
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))
        style.configure("Secondary.TButton", font=("Segoe UI", 10))
        
        bg_btn = ttk.Button(button_frame, text="Chọn ảnh nền", 
                           command=self._select_bg_image, style="Secondary.TButton")
        bg_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.start_btn = ttk.Button(button_frame, text="Bắt đầu", 
                                   command=self._start, style="Accent.TButton")
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(button_frame, text="Dừng", 
                                  command=self._stop, state=tk.DISABLED, style="Secondary.TButton")
        self.stop_btn.pack(side=tk.LEFT)

    def _build_log(self, parent: tk.Widget) -> None:
        # Header
        header_frame = tk.Frame(parent, bg="white")
        header_frame.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        label = tk.Label(header_frame, text="Nhật ký hoạt động", 
                        font=("Segoe UI", 12, "bold"), 
                        fg="#2c3e50", bg="white")
        label.pack(anchor="w")

        # Text area with scrollbar
        text_frame = tk.Frame(parent, bg="white")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)

        self.log_text = tk.Text(text_frame, height=8, wrap=tk.WORD, state=tk.DISABLED, 
                               font=("Consolas", 9), bg="#f8f9fa", fg="#2c3e50",
                               relief="flat", bd=0, padx=10, pady=8)
        yscroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=yscroll.set)

        self.log_text.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")

    # Background drawing (simplified for modern design)
    def _draw_background(self) -> None:
        # Background is now handled by the main container's bg color
        # This method is kept for compatibility but simplified
        pass

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
            # Apply background image to main container
            self._apply_background_image()
            self._log(f"Đã đặt ảnh nền: {os.path.basename(path)}")
        except Exception as exc:
            messagebox.showerror("Lỗi ảnh nền", f"Không thể mở ảnh: {exc}")

    def _apply_background_image(self) -> None:
        """Apply background image to the main container"""
        if self.bg_pil_image is not None and PIL_AVAILABLE:
            # Create a subtle background effect
            w = self.main_container.winfo_width()
            h = self.main_container.winfo_height()
            if w > 1 and h > 1:
                # Resize image to fit container with opacity effect
                img_w, img_h = self.bg_pil_image.size
                if img_w > 0 and img_h > 0:
                    # Scale to fit container
                    scale = min(w / img_w, h / img_h)
                    new_w = max(1, int(img_w * scale))
                    new_h = max(1, int(img_h * scale))
                    resized = self.bg_pil_image.resize((new_w, new_h), Image.LANCZOS)
                    
                    # Apply subtle opacity (make it more transparent)
                    resized.putalpha(30)  # Very subtle background
                    
                    self.bg_tk_image = ImageTk.PhotoImage(resized)
                    # Apply as background to main container
                    self.main_container.configure(bg="#f0f2f5")  # Keep light background

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
        """Run the captcha workflow in a background thread. Can run all supported domains sequentially."""
        username = self.username_var.get().strip()
        lang = self.lang_var.get().strip() or "vi-VN"
        selected_domain = (self.site_var.get().strip() or "mmoocode.shop").replace("https://", "").replace("http://", "").strip("/")
        if selected_domain == "link1.789pcode.win":
            selected_domain = "789pcode.store"
        promo_code = self.promo_var.get().strip() or "TAIAPP"
        run_both = bool(self.run_both_var.get())
        proxy_url = self.proxy_var.get().strip() or None

        supported_domains: list[str] = [
            "mmoocode.shop",
            "go99code.store",
            "tt88code.win",
            "nohucode.shop",
            "789pcode.store",
        ]
        domains_to_run: list[str] = supported_domains if run_both else [selected_domain]

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
        def extract_nonces_with_fallback(client, base_url: str, html: str) -> tuple[str | None, str | None]:
            candidates: list[str] = []
            patterns = [
                r"ajax\.php'\s*;\s*const\s+nonce=['\"]([A-Za-z0-9]+)['\"]",
                r"const\s+nonce=['\"]([A-Za-z0-9]+)['\"]",
                r"nonce\s*[:=]\s*['\"]([A-Za-z0-9]+)['\"]",
                r"\"nonce\"\s*:\s*\"([A-Za-z0-9]+)\"",
            ]
            for pat in patterns:
                for val in re.findall(pat, html):
                    if val not in candidates:
                        candidates.append(val)
            if len(candidates) < 2:
                script_srcs = re.findall(r"<script[^>]+src=['\"]([^'\"]+\.js)['\"]", html, flags=re.IGNORECASE)
                seen: set[str] = set()
                base_netloc = urlparse(base_url).netloc
                for src in script_srcs[:10]:  # limit
                    js_url = urljoin(base_url + '/', src)
                    # Same-origin only
                    try:
                        parsed = urlparse(js_url)
                        if parsed.netloc and parsed.netloc != base_netloc:
                            continue
                    except Exception:
                        pass
                    if js_url in seen:
                        continue
                    seen.add(js_url)
                    try:
                        js_body = client.get(js_url, timeout=15).text
                    except Exception:
                        continue
                    for pat in patterns:
                        for val in re.findall(pat, js_body):
                            if val not in candidates:
                                candidates.append(val)
                            if len(candidates) >= 2:
                                break
                        if len(candidates) >= 2:
                            break
            if not candidates:
                return None, None
            if len(candidates) == 1:
                return candidates[0], candidates[0]
            return candidates[0], candidates[1]

        try:
            for domain in domains_to_run:
                if check_stop():
                    break

                base_url = f"https://{domain}"
                self._log(f"--- Chạy cho: {domain} ---")

                # Prepare session
                client = requests.Session()
                # Apply proxies if provided
                if proxy_url:
                    proxies = {"http": proxy_url, "https": proxy_url}
                    try:
                        client.proxies.update(proxies)
                        self._log(f"Đang sử dụng proxy cho {domain}")
                    except Exception as px:
                        self._log(f"Không áp dụng được proxy: {px}")
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

                # 1) Get nonce values from homepage (with fallbacks)
                self._log("Đang lấy nonce…")
                try:
                    home_html = client.get(base_url + '/', timeout=25).text
                except Exception as exc_home:
                    self._log(f"Không truy cập được trang chủ: {exc_home}")
                    continue

                nonce1, nonce2 = extract_nonces_with_fallback(client, base_url, home_html)
                if not nonce1 or not nonce2:
                    # Fallback for known domains
                    if domain == "tt88code.win":
                        nonce1 = nonce1 or "7bb988d5ca"
                        nonce2 = nonce2 or "2279debe40"
                        self._log("Dùng nonce fallback cho tt88code.win.")
                    elif domain == "nohucode.shop":
                        nonce1 = nonce1 or "6eb9a33928"
                        nonce2 = nonce2 or "4043c812cf"
                        self._log("Dùng nonce fallback cho nohucode.shop.")
                    elif domain == "789pcode.store":
                        nonce1 = nonce1 or "526f7b10f9"
                        nonce2 = nonce2 or "158506ad59"
                        self._log("Dùng nonce fallback cho 789pcode.store.")
                    else:
                        self._log("Không trích xuất được nonce. Có thể giao diện trang đã thay đổi.")
                        continue

                self._log(f"nonce1={nonce1}")
                self._log(f"nonce2={nonce2}")

                if check_stop():
                    break

                # 2) Call taiApp
                self._log("Gọi get_promo_verification_type…")
                try:
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
                except Exception as exc_ta:
                    self._log(f"Lỗi gọi get_promo_verification_type: {exc_ta}")
                    continue

                if check_stop():
                    break

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
                try:
                    response = client.post(f'{base_url}/wp-admin/admin-ajax.php', data=payload, timeout=20)
                except Exception as exc_cap:
                    self._log(f"Lỗi yêu cầu audio captcha: {exc_cap}")
                    continue

                audio_url = None
                try:
                    res_json = response.json()
                    if res_json.get("success") and "data" in res_json and "audio_url" in res_json["data"]:
                        audio_url = res_json["data"]["audio_url"].replace("\\/", "/")
                except Exception:
                    pass

                if not audio_url:
                    self._log("Không nhận được audio_url từ server.")
                    self.root.after(0, lambda: messagebox.showerror("Lỗi", "Không nhận được audio_url từ server. Có thể tên tài khoản hoặc mã khuyến mãi không hợp lệ."))
                    continue

                # Normalize audio URL to absolute
                if not audio_url.startswith("http://") and not audio_url.startswith("https://"):
                    audio_url = urljoin(base_url + '/', audio_url.lstrip('/'))
                self._log(f"audio_url: {audio_url}")

                if check_stop():
                    break

                # 4) STT to digits
                self._log("Đang nhận dạng giọng nói…")
                code = speech_to_text_from_url(audio_url, speech_lang=lang, session=client)
                self._log(f"Mã nhận dạng: {code}")
                if not code:
                    self._log("Không nhận dạng được mã captcha.")
                    self.root.after(0, lambda: messagebox.showwarning("Lỗi", "Không nhận dạng được mã captcha từ audio."))
                    continue

                if check_stop():
                    break

                # 5) Verify audio captcha
                self._log("Xác minh mã captcha…")
                try:
                    verify_res = client.post(
                        f'{base_url}/wp-admin/admin-ajax.php',
                        data={
                            'action': 'verify_audio_captcha',
                            'nonce': nonce2,
                            'captcha_input': code,
                        },
                        timeout=20,
                    ).text
                except Exception as exc_ver:
                    self._log(f"Lỗi verify captcha: {exc_ver}")
                    continue
                self._log(f"KQ verify: {verify_res}")

                try:
                    verify_json = json.loads(verify_res)
                    if not verify_json.get("success"):
                        msg = verify_json.get("data", {}).get("message", "Mã xác thực không đúng")
                        self._log("Xác minh captcha thất bại.")
                        self.root.after(0, lambda: messagebox.showerror("Lỗi", f"Xác minh captcha thất bại: {msg}"))
                        continue
                except Exception:
                    self._log("Không đọc được KQ verify, tiếp tục gửi form…")

                if check_stop():
                    break

                # 6) Final form submit
                self._log("Gửi form cuối…")
                try:
                    final_res = client.post(
                        base_url + '/',
                        data={
                            'ten_tai_khoan': username,
                            'ma_khuyen_mai': promo_code,
                            'captcha': '',
                        },
                        timeout=20,
                    ).text
                except Exception as exc_fin:
                    self._log(f"Lỗi gửi form cuối: {exc_fin}")
                    continue

                final_msg_clean = "Không trích xuất được thông báo."
                try:
                    m_err = re.search(r"showFormError\s*\(\s*['\"](.*?)['\"]\s*\)", final_res, re.DOTALL)
                    m_succ = re.search(r"showFormSuccess\s*\(\s*['\"](.*?)['\"]\s*\)", final_res, re.DOTALL)
                    if m_succ:
                        final_msg_clean = f"THÀNH CÔNG: {m_succ.group(1)}"
                        self.root.after(0, lambda: messagebox.showinfo("Thành công", m_succ.group(1)))
                    elif m_err:
                        final_msg_clean = f"LỖI: {m_err.group(1)}"
                        self.root.after(0, lambda: messagebox.showerror("Lỗi", m_err.group(1)))
                    else:
                        final_msg_clean = final_res[:400] + ("…" if len(final_res) > 400 else "")
                except Exception:
                    final_msg_clean = final_res[:400] + ("…" if len(final_res) > 400 else "")
                self._log(f"KQ cuối: {final_msg_clean}")

        except Exception as e:
            self._log("Đã xảy ra lỗi không mong muốn.")
            self._log(str(e))
            tb = traceback.format_exc(limit=3)
            self._log(tb)
            self.root.after(0, lambda: messagebox.showerror("Lỗi nghiêm trọng", str(e)))
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
    
    # Configure modern styling
    try:
        style = ttk.Style(root)
        # Use a modern theme
        for theme in ("vista", "clam", "alt", "default"):
            if theme in style.theme_names():
                style.theme_use(theme)
                break
        
        # Customize ttk styles for modern look
        style.configure("TCombobox", fieldbackground="white", borderwidth=1)
        style.configure("TEntry", fieldbackground="white", borderwidth=1)
        style.configure("TButton", padding=(10, 5))
        style.configure("Accent.TButton", padding=(12, 6))
        style.configure("Secondary.TButton", padding=(10, 5))
        style.configure("TCheckbutton", font=("Segoe UI", 10))
        
    except Exception:
        pass

    # Set window icon and properties
    root.resizable(True, True)
    
    app = CaptchaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
