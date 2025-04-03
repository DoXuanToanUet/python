import sys
import time
import random
import threading
import json
import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QSpinBox, QProgressBar, QTextEdit, QFrame, QTabWidget,
                             QRadioButton, QCheckBox)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

# -----------------------------------------------
# WorkerSignals: giao tiếp giữa thread và UI
# -----------------------------------------------
class WorkerSignals(QObject):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal()
    history_update = pyqtSignal(dict)
    session_update = pyqtSignal(dict)

# -----------------------------------------------
# Lớp YouTubeAutomator: tự động hóa thao tác trên YouTube
# -----------------------------------------------
class YouTubeAutomator:
    def __init__(self, signals, comment_templates=None):
        self.signals = signals

        options = Options()
        options.add_experimental_option("debuggerAddress", "localhost:9222")
        self.signals.log.emit("Connecting to Chrome browser...")
        try:
            self.driver = webdriver.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 10)
            self.signals.log.emit("Successfully connected to Chrome browser")
        except Exception as e:
            self.signals.log.emit(f"Error connecting to Chrome: {e}")
            raise

        if comment_templates is not None:
            self.comment_templates = [line.strip() for line in comment_templates.splitlines() if line.strip()]
        else:
            self.comment_templates = [
                "Video rất hay, cảm ơn bạn đã chia sẻ!",
                "Nội dung tuyệt vời, tôi đã học được nhiều điều!",
                "Chất lượng video rất tốt, mong chờ các video tiếp theo!",
                "Cảm ơn vì nội dung hữu ích!",
                "Tôi thích video này, đã đăng ký kênh của bạn!"
            ]

    def get_channel_videos(self, channel_url):
        self.signals.log.emit(f"Navigating to channel: {channel_url}")
        videos_url = channel_url + "/videos"
        self.driver.get(videos_url)
        time.sleep(3)
        self.signals.log.emit("Scrolling to load more videos...")
        for i in range(5):
            self.driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            self.signals.log.emit(f"Scroll {i+1}/5 completed")
            time.sleep(2)
        self.signals.log.emit("Collecting video links...")
        video_elements = self.driver.find_elements(By.CSS_SELECTOR, "a#video-title-link")
        video_urls = [elem.get_attribute('href') for elem in video_elements if elem.get_attribute('href')]
        video_titles = [elem.get_attribute('title') for elem in video_elements if elem.get_attribute('href')]
        video_info = list(zip(video_urls, video_titles))
        self.signals.log.emit(f"Found {len(video_info)} videos from channel")
        return video_info

    def like_and_comment(self, video_url, video_title, session_id, do_like=True, do_comment=True):
        self.signals.log.emit(f"Opening video: {video_url}")
        self.signals.log.emit(f"Title: {video_title}")
        self.driver.get(video_url)
        result = {
            "url": video_url,
            "title": video_title,
            "liked": False,
            "commented": False,
            "comment_text": "",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "session_id": session_id
        }
        try:
            time.sleep(5)
            if do_like:
                try:
                    like_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".ytLikeButtonViewModelHost")))
                    like_button.click()
                    self.signals.log.emit("✅ Liked video")
                    result["liked"] = True
                    time.sleep(1)
                except (TimeoutException, NoSuchElementException):
                    self.signals.log.emit("⚠️ Like button not found")
            if do_comment:
                try:
                    self.driver.execute_script("window.scrollBy(0, 500);")
                    time.sleep(2)
                    comment_box = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#simplebox-placeholder")))
                    comment_box.click()
                    time.sleep(1)
                    comment_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#contenteditable-root")))
                    random_comment = random.choice(self.comment_templates)
                    comment_input.send_keys(random_comment)
                    result["comment_text"] = random_comment
                    time.sleep(1)
                    submit_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#submit-button")))
                    submit_button.click()
                    self.signals.log.emit(f"✅ Posted comment: '{random_comment}'")
                    result["commented"] = True
                    time.sleep(2)
                except (TimeoutException, NoSuchElementException) as e:
                    self.signals.log.emit(f"⚠️ Error commenting: {e}")
            self.signals.history_update.emit(result)
            return result
        except Exception as e:
            self.signals.log.emit(f"❌ Error processing video {video_url}: {e}")
            self.signals.history_update.emit(result)
            return result

    def process_channel(self, channel_url, max_videos=None, delay_between_videos=30, do_like=True, do_comment=True):
        session_id = f"session_{int(time.time())}"
        session_history = {
            "session_id": session_id,
            "channel_url": channel_url,
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "videos": []
        }
        self.signals.session_update.emit(session_history)
        try:
            video_info = self.get_channel_videos(channel_url)
            try:
                channel_name = self.driver.find_element(By.ID, "channel-name").text
                session_history["channel_name"] = channel_name
                self.signals.log.emit(f"Channel name: {channel_name}")
            except Exception:
                session_history["channel_name"] = "Unknown Channel"
            if max_videos and max_videos < len(video_info):
                video_info = video_info[:max_videos]
                self.signals.log.emit(f"Limited to first {max_videos} videos")
            processed_videos = []
            total = len(video_info)
            for i, (url, title) in enumerate(video_info):
                self.signals.log.emit(f"\n📺 Processing video {i+1}/{total}")
                video_result = self.like_and_comment(url, title, session_id, do_like, do_comment)
                processed_videos.append(video_result)
                session_history["videos"].append(url)
                progress_percent = int((i + 1) / total * 100)
                self.signals.progress.emit(progress_percent)
                if i < total - 1:
                    self.signals.log.emit(f"⏱️ Waiting {delay_between_videos} seconds before next video...")
                    time.sleep(delay_between_videos)
            session_history["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            session_history["videos_processed"] = total
            session_history["processed_videos"] = processed_videos
            session_history["status"] = "completed"
            self.signals.session_update.emit(session_history)
            self.signals.log.emit("\n✅ All videos processed successfully!")
            self.signals.progress.emit(100)
            self.signals.finished.emit()
        except Exception as e:
            self.signals.log.emit(f"❌ Error: {e}")
            session_history["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            session_history["error"] = str(e)
            session_history["status"] = "error"
            self.signals.session_update.emit(session_history)
            self.signals.finished.emit()

    def process_video_list(self, video_list, delay_between_videos=30, do_like=True, do_comment=True):
        session_id = f"session_{int(time.time())}"
        session_history = {
            "session_id": session_id,
            "video_list": video_list,
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "videos": []
        }
        self.signals.session_update.emit(session_history)
        processed_videos = []
        total = len(video_list)
        for i, url in enumerate(video_list):
            self.signals.log.emit(f"\n📺 Processing video {i+1}/{total}")
            video_result = self.like_and_comment(url, url, session_id, do_like, do_comment)
            processed_videos.append(video_result)
            session_history["videos"].append(url)
            progress_percent = int((i + 1) / total * 100)
            self.signals.progress.emit(progress_percent)
            if i < total - 1:
                self.signals.log.emit(f"⏱️ Waiting {delay_between_videos} seconds before next video...")
                time.sleep(delay_between_videos)
        session_history["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session_history["videos_processed"] = total
        session_history["processed_videos"] = processed_videos
        session_history["status"] = "completed"
        self.signals.session_update.emit(session_history)
        self.signals.log.emit("\n✅ All videos processed successfully!")
        self.signals.progress.emit(100)
        self.signals.finished.emit()

# -----------------------------------------------
# Lớp HistoryManager: quản lý lịch sử xử lý
# -----------------------------------------------
class HistoryManager:
    def __init__(self):
        self.history_file = "youtube_automator_history.json"
        self.history = self.load_history()

    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as file:
                    return json.load(file)
            except Exception:
                return {"sessions": [], "videos": []}
        else:
            return {"sessions": [], "videos": []}

    def save_history(self):
        with open(self.history_file, 'w', encoding='utf-8') as file:
            json.dump(self.history, file, ensure_ascii=False, indent=2)

    def add_video_interaction(self, video_data):
        self.history["videos"].append(video_data)
        self.save_history()

    def add_session(self, session_data):
        session_id = session_data.get("session_id")
        if not session_id:
            self.history["sessions"].append(session_data)
        else:
            for i, session in enumerate(self.history["sessions"]):
                if session.get("session_id") == session_id:
                    self.history["sessions"][i] = session_data
                    break
            else:
                self.history["sessions"].append(session_data)
        self.save_history()

    def get_history(self):
        return self.history

    def get_session_videos(self, session_id):
        return [video for video in self.history["videos"] if video.get("session_id") == session_id]

# -----------------------------------------------
# Lớp giao diện chính YouTubeAutomationUI
# -----------------------------------------------
class YouTubeAutomationUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Channel Automator")
        self.setMinimumSize(850, 750)
        self.worker_thread = None
        self.worker_signals = WorkerSignals()
        self.worker_signals.progress.connect(self.update_progress)
        self.worker_signals.log.connect(self.append_log)
        self.worker_signals.finished.connect(self.on_process_finished)
        self.worker_signals.history_update.connect(self.update_history)
        self.worker_signals.session_update.connect(self.update_session)
        self.history_manager = HistoryManager()
        self.initUI()

    def initUI(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        title_label = QLabel("YouTube Channel Automator")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Arial", 20, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #FF0000; margin: 10px;")
        main_layout.addWidget(title_label)

        desc_label = QLabel("Tự động like và bình luận trên video từ kênh hoặc danh sách URL")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #555; font-size: 14px; margin-bottom: 15px; height:100px;")
        main_layout.addWidget(desc_label)

        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # --- Tab Process ---
        process_tab = QWidget()
        process_layout = QVBoxLayout()
        process_tab.setLayout(process_layout)

        form_container = QWidget()
        form_container.setStyleSheet("background-color: #f5f5f5; border-radius: 10px; padding: 20px;")
        form_layout = QVBoxLayout()
        form_container.setLayout(form_layout)

        # Chế độ xử lý: Channel URL hoặc Danh sách URL
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Chế độ xử lý:")
        self.radio_channel = QRadioButton("Channel URL")
        self.radio_list = QRadioButton("Danh sách URL")
        self.radio_channel.setChecked(True)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.radio_channel)
        mode_layout.addWidget(self.radio_list)
        form_layout.addLayout(mode_layout)

        # Nhập Channel URL
        self.channel_url_layout = QHBoxLayout()
        channel_label = QLabel("Channel URL:")
        channel_label.setMinimumWidth(120)
        channel_label.setFixedHeight(30)  # Set your desired height here
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/@channelname")
        self.channel_url_layout.addWidget(channel_label)
        self.channel_url_layout.addWidget(self.url_input)
        form_layout.addLayout(self.channel_url_layout)

        # Nhập Danh sách URL
        self.list_url_layout = QVBoxLayout()
        self.list_label = QLabel("Danh sách URL (mỗi dòng 1 URL):")
        self.list_url_text = QTextEdit()
        self.list_url_text.setPlaceholderText("https://www.youtube.com/...\nhttps://www.youtube.com/...")
        self.list_url_layout.addWidget(self.list_label)
        self.list_url_layout.addWidget(self.list_url_text)
        form_layout.addLayout(self.list_url_layout)
        self.list_label.hide()
        self.list_url_text.hide()
        self.radio_channel.toggled.connect(self.toggle_mode)
        self.radio_list.toggled.connect(self.toggle_mode)

        # Cài đặt: Max Videos (Channel URL) và Delay
        settings_layout = QHBoxLayout()
        max_videos_layout = QHBoxLayout()
        max_videos_label = QLabel("Max Videos:")
        self.max_videos_input = QSpinBox()
        self.max_videos_input.setRange(1, 100)
        self.max_videos_input.setValue(10)
        max_videos_layout.addWidget(max_videos_label)
        max_videos_layout.addWidget(self.max_videos_input)
        settings_layout.addLayout(max_videos_layout)
        delay_layout = QHBoxLayout()
        delay_label = QLabel("Delay (seconds):")
        self.delay_input = QSpinBox()
        self.delay_input.setRange(10, 300)
        self.delay_input.setValue(30)
        delay_layout.addWidget(delay_label)
        delay_layout.addWidget(self.delay_input)
        settings_layout.addLayout(delay_layout)
        form_layout.addLayout(settings_layout)

        # Lựa chọn hành động: sử dụng 3 checkbox: All, Like, Comment
        action_layout = QHBoxLayout()
        action_label = QLabel("Hành động:")
        self.checkbox_all = QCheckBox("All")
        self.checkbox_like = QCheckBox("Like")
        self.checkbox_comment = QCheckBox("Comment")
        self.checkbox_all.setChecked(True)
        self.checkbox_like.setChecked(True)
        self.checkbox_comment.setChecked(True)
        self.checkbox_like.setEnabled(False)
        self.checkbox_comment.setEnabled(False)
        self.checkbox_all.stateChanged.connect(self.update_action_checkboxes)
        action_layout.addWidget(action_label)
        action_layout.addWidget(self.checkbox_all)
        action_layout.addWidget(self.checkbox_like)
        action_layout.addWidget(self.checkbox_comment)
        form_layout.addLayout(action_layout)

        # Nút Start và Stop
        btn_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Process")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white; border: none;
                border-radius: 5px; padding: 10px 20px; font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        self.start_button.clicked.connect(self.start_process)
        self.stop_button = QPushButton("Stop")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336; color: white; border: none;
                border-radius: 5px; padding: 10px 20px; font-weight: bold;
            }
            QPushButton:hover { background-color: #d32f2f; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        self.stop_button.clicked.connect(self.stop_process)
        self.stop_button.setEnabled(False)
        btn_layout.addWidget(self.start_button)
        btn_layout.addWidget(self.stop_button)
        form_layout.addLayout(btn_layout)

        process_layout.addWidget(form_container)

        # Thanh progress
        progress_frame = QFrame()
        progress_frame.setFrameShape(QFrame.StyledPanel)
        progress_frame.setStyleSheet("border: 1px solid #ddd; border-radius: 5px; background-color: white; padding: 10px;")
        progress_layout = QVBoxLayout()
        progress_frame.setLayout(progress_layout)
        progress_label = QLabel("Progress:")
        progress_layout.addWidget(progress_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: 1px solid #bbb; border-radius: 5px; text-align: center; height: 25px; }
            QProgressBar::chunk { background-color: #4CAF50; border-radius: 5px; }
        """)
        progress_layout.addWidget(self.progress_bar)
        process_layout.addWidget(progress_frame)

        # Log hoạt động
        log_frame = QFrame()
        log_frame.setFrameShape(QFrame.StyledPanel)
        log_frame.setStyleSheet("border: 1px solid #ddd; border-radius: 5px; background-color: white; padding: 10px;")
        log_layout = QVBoxLayout()
        log_frame.setLayout(log_layout)
        log_label = QLabel("Activity Log:")
        log_layout.addWidget(log_label)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px;")
        log_layout.addWidget(self.log_text)
        process_layout.addWidget(log_frame)

        self.tab_widget.addTab(process_tab, "Process")

        # --- Tab History ---
        history_tab = QWidget()
        history_layout = QVBoxLayout()
        history_tab.setLayout(history_layout)
        history_label = QLabel("Processing History:")
        history_label.setFont(QFont("Arial", 12, QFont.Bold))
        history_layout.addWidget(history_label)
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px;")
        history_layout.addWidget(self.history_text)
        refresh_button = QPushButton("Refresh History")
        refresh_button.clicked.connect(self.display_history)
        history_layout.addWidget(refresh_button)
        self.tab_widget.addTab(history_tab, "History")

        # --- Tab Mẫu Bình Luận ---
        comment_tab = QWidget()
        comment_layout = QVBoxLayout()
        comment_tab.setLayout(comment_layout)
        comment_label = QLabel("Nhập mẫu bình luận (mỗi dòng là 1 mẫu):")
        comment_label.setFont(QFont("Arial", 12, QFont.Bold))
        comment_layout.addWidget(comment_label)
        self.template_text_edit = QTextEdit()
        self.template_text_edit.setStyleSheet("QTextEdit { line-height: 150%; font-size: 14px; }")
        default_templates_text = (
            "Video rất hay, cảm ơn bạn đã chia sẻ!\n"
            "Nội dung tuyệt vời, tôi đã học được nhiều điều!\n"
            "Chất lượng video rất tốt, mong chờ các video tiếp theo!\n"
            "Cảm ơn vì nội dung hữu ích!\n"
            "Tôi thích video này, đã đăng ký kênh của bạn!"
        )
        self.template_text_edit.setPlainText(default_templates_text)
        comment_layout.addWidget(self.template_text_edit)
        self.tab_widget.addTab(comment_tab, "Mẫu Bình Luận")

        footer_label = QLabel('Copyright by toanAI- <a href="http://doxuantoan.com">doxuantoandotcom</a>')
        footer_label.setOpenExternalLinks(True)
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("color: #555; margin-top: 10px;")
        main_layout.addWidget(footer_label)

        self.statusBar().showMessage("Ready")
        self.display_history()

    def update_action_checkboxes(self):
        if self.checkbox_all.isChecked():
            self.checkbox_like.setChecked(True)
            self.checkbox_comment.setChecked(True)
            self.checkbox_like.setEnabled(False)
            self.checkbox_comment.setEnabled(False)
        else:
            self.checkbox_like.setEnabled(True)
            self.checkbox_comment.setEnabled(True)

    def toggle_mode(self):
        if self.radio_channel.isChecked():
            self.url_input.show()
            for i in range(self.channel_url_layout.count()):
                widget = self.channel_url_layout.itemAt(i).widget()
                if widget:
                    widget.show()
            self.list_label.hide()
            self.list_url_text.hide()
        else:
            self.url_input.hide()
            for i in range(self.channel_url_layout.count()):
                widget = self.channel_url_layout.itemAt(i).widget()
                if widget:
                    widget.hide()
            self.list_label.show()
            self.list_url_text.show()

    def display_history(self):
        history_data = self.history_manager.get_history()
        self.history_text.clear()
        if not history_data["sessions"]:
            self.history_text.append("Chưa có lịch sử nào.")
            return
        sorted_sessions = sorted(
            history_data["sessions"], 
            key=lambda x: datetime.strptime(x.get("start_time", "2000-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S"),
            reverse=True
        )
        self.history_text.append("### LỊCH SỬ PHIÊN LÀM VIỆC ###\n")
        for i, session in enumerate(sorted_sessions[:20]):
            session_start = session.get("start_time", "Không rõ")
            session_end = session.get("end_time", "Đang chạy")
            channel_url = session.get("channel_url", session.get("video_list", "Không xác định"))
            channel_name = session.get("channel_name", "Tên kênh không xác định")
            session_id = session.get("session_id", "")
            self.history_text.append(f"Phiên #{i+1} - {session_start}")
            self.history_text.append(f"Kênh/URL: {channel_url}")
            self.history_text.append(f"Thời gian kết thúc: {session_end}")
            status = session.get("status", "unknown")
            if status == "error":
                error_msg = session.get("error", "Không rõ lỗi")
                self.history_text.append(f"Trạng thái: ❌ Lỗi - {error_msg}")
            elif status == "completed":
                self.history_text.append("Trạng thái: ✅ Hoàn thành")
            else:
                self.history_text.append(f"Trạng thái: ⏳ {status}")
            videos_processed = session.get("videos_processed", 0)
            self.history_text.append(f"Số video đã xử lý: {videos_processed}")
            session_videos = self.history_manager.get_session_videos(session_id)
            liked_count = sum(1 for v in session_videos if v.get("liked", False))
            commented_count = sum(1 for v in session_videos if v.get("commented", False))
            self.history_text.append(f"Đã like: {liked_count} video")
            self.history_text.append(f"Đã bình luận: {commented_count} video")
            if session_videos:
                self.history_text.append("\nChi tiết video:")
                for j, video in enumerate(session_videos):
                    self.history_text.append(f"  {j+1}. {video.get('title', 'Tiêu đề không xác định')}")
                    self.history_text.append(f"     Like: {'✅' if video.get('liked', False) else '❌'}")
                    self.history_text.append(f"     Bình luận: {'✅' if video.get('commented', False) else '❌'}")
                    if video.get('commented', False):
                        comment = video.get('comment_text', '')
                        if len(comment) > 50:
                            comment = comment[:47] + "..."
                        self.history_text.append(f"     Nội dung: \"{comment}\"")
            self.history_text.append("=" * 50 + "\n")

    def append_log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.append(formatted_message)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        self.statusBar().showMessage(f"Progress: {value}%")

    def update_history(self, video_data):
        self.history_manager.add_video_interaction(video_data)

    def update_session(self, session_data):
        self.history_manager.add_session(session_data)

    def get_comment_templates(self):
        return self.template_text_edit.toPlainText()

    def get_action_flags(self):
        if self.checkbox_all.isChecked():
            return True, True
        else:
            return self.checkbox_like.isChecked(), self.checkbox_comment.isChecked()

    def start_process(self):
        do_like, do_comment = self.get_action_flags()
        delay_between_videos = self.delay_input.value()
        max_videos = self.max_videos_input.value()
        templates = self.get_comment_templates()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.append_log("Bắt đầu xử lý...")

        if self.radio_channel.isChecked():
            channel_url = self.url_input.text().strip()
            if not channel_url:
                self.append_log("❌ Vui lòng nhập URL kênh hợp lệ")
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                return
            if not (channel_url.startswith("https://www.youtube.com/") or channel_url.startswith("https://youtube.com/")):
                self.append_log("❌ Định dạng URL YouTube không hợp lệ")
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                return
            self.append_log(f"Cài đặt: Channel URL={channel_url}, Max Videos={max_videos}, Delay={delay_between_videos}s")
            self.worker_thread = threading.Thread(
                target=self.run_channel_mode,
                args=(channel_url, max_videos, delay_between_videos, do_like, do_comment, templates)
            )
        else:
            list_text = self.list_url_text.toPlainText().strip()
            if not list_text:
                self.append_log("❌ Vui lòng nhập danh sách URL hợp lệ")
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                return
            video_list = [line.strip() for line in list_text.splitlines() if line.strip()]
            self.append_log(f"Cài đặt: Danh sách URL gồm {len(video_list)} video, Delay={delay_between_videos}s")
            self.worker_thread = threading.Thread(
                target=self.run_list_mode,
                args=(video_list, delay_between_videos, do_like, do_comment, templates)
            )
        self.worker_thread.daemon = True
        self.worker_thread.start()

    def run_channel_mode(self, channel_url, max_videos, delay_between_videos, do_like, do_comment, templates):
        try:
            automator = YouTubeAutomator(self.worker_signals, comment_templates=templates)
            automator.process_channel(
                channel_url=channel_url,
                max_videos=max_videos,
                delay_between_videos=delay_between_videos,
                do_like=do_like,
                do_comment=do_comment
            )
        except Exception as e:
            self.worker_signals.log.emit(f"❌ Lỗi nghiêm trọng: {e}")
            self.worker_signals.finished.emit()

    def run_list_mode(self, video_list, delay_between_videos, do_like, do_comment, templates):
        try:
            automator = YouTubeAutomator(self.worker_signals, comment_templates=templates)
            automator.process_video_list(
                video_list=video_list,
                delay_between_videos=delay_between_videos,
                do_like=do_like,
                do_comment=do_comment
            )
        except Exception as e:
            self.worker_signals.log.emit(f"❌ Lỗi nghiêm trọng: {e}")
            self.worker_signals.finished.emit()

    def stop_process(self):
        if self.worker_thread and self.worker_thread.is_alive():
            self.append_log("🛑 Đang dừng tiến trình... (có thể mất một lúc)")
            self.on_process_finished()

    def on_process_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.statusBar().showMessage("Ready")
        self.display_history()

    def closeEvent(self, event):
        if self.worker_thread and self.worker_thread.is_alive():
            self.append_log("Đang đóng ứng dụng...")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = YouTubeAutomationUI()
    window.show()
    sys.exit(app.exec_())
