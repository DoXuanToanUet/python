from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QSpinBox, QProgressBar, QTextEdit, QFrame, QTabWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import threading
import time
from datetime import datetime

from utils.signals import WorkerSignals
from history_manager import HistoryManager
from automator import YouTubeAutomator

class YouTubeAutomationUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Channel Automator")
        self.setMinimumSize(800, 600)
        
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
        main_layout.setSpacing(20)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        title_label = QLabel("YouTube Channel Automator")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Arial", 18, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #FF0000; margin: 10px;")
        main_layout.addWidget(title_label)
        
        desc_label = QLabel("Automatically like and comment on videos from a YouTube channel")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #555; font-size: 14px; margin-bottom: 20px;")
        main_layout.addWidget(desc_label)
        
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # --- Tab Process ---
        main_tab = QWidget()
        main_tab_layout = QVBoxLayout()
        main_tab.setLayout(main_tab_layout)
        
        form_container = QWidget()
        form_container.setStyleSheet("background-color: #f5f5f5; border-radius: 10px; padding: 20px;")
        form_layout = QVBoxLayout()
        form_container.setLayout(form_layout)
        
        url_layout = QHBoxLayout()
        url_label = QLabel("Channel URL:")
        url_label.setMinimumWidth(120)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/@channelname")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        form_layout.addLayout(url_layout)
        
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
        
        buttons_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Process")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.start_button.clicked.connect(self.start_process)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.stop_button.clicked.connect(self.stop_process)
        self.stop_button.setEnabled(False)
        
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        form_layout.addLayout(buttons_layout)
        
        main_tab_layout.addWidget(form_container)
        
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
            QProgressBar {
                border: 1px solid #bbb;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 5px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        main_tab_layout.addWidget(progress_frame)
        
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
        
        main_tab_layout.addWidget(log_frame)
        self.tab_widget.addTab(main_tab, "Process")
        
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
        template_tab = QWidget()
        template_layout = QVBoxLayout()
        template_tab.setLayout(template_layout)
        
        template_label = QLabel("Nhập mẫu bình luận (mỗi dòng là 1 mẫu):")
        template_label.setFont(QFont("Arial", 12, QFont.Bold))
        template_layout.addWidget(template_label)
        
        self.template_text_edit = QTextEdit()
        default_templates_text = (
            "Video rất hay, cảm ơn bạn đã chia sẻ!\n"
            "Nội dung tuyệt vời, tôi đã học được nhiều điều!\n"
            "Chất lượng video rất tốt, mong chờ các video tiếp theo!\n"
            "Cảm ơn vì nội dung hữu ích!\n"
            "Tôi thích video này, đã đăng ký kênh của bạn!"
        )
        self.template_text_edit.setPlainText(default_templates_text)
        template_layout.addWidget(self.template_text_edit)
        self.tab_widget.addTab(template_tab, "Mẫu Bình Luận")
        
        footer_label = QLabel()
        footer_label.setText('Copyright by toanAI- <a href="http://doxuantoan.com">doxuantoandotcom</a>')
        footer_label.setOpenExternalLinks(True)
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("color: #555; margin-top: 10px;")
        main_layout.addWidget(footer_label)
        
        self.statusBar().showMessage("Ready")
        self.display_history()
    
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
            channel_url = session.get("channel_url", "Kênh không xác định")
            channel_name = session.get("channel_name", "Tên kênh không xác định")
            session_id = session.get("session_id", "")
            
            self.history_text.append(f"Phiên #{i+1} - {session_start}")
            self.history_text.append(f"Kênh: {channel_name}")
            self.history_text.append(f"URL: {channel_url}")
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
        """Lấy nội dung mẫu bình luận từ QTextEdit (dạng đa dòng)"""
        return self.template_text_edit.toPlainText()
    
    def start_process(self):
        channel_url = self.url_input.text().strip()
        if not channel_url:
            self.append_log("❌ Vui lòng nhập URL kênh hợp lệ")
            return
        
        if not (channel_url.startswith("https://www.youtube.com/") or 
                channel_url.startswith("https://youtube.com/")):
            self.append_log("❌ Định dạng URL YouTube không hợp lệ")
            return
        
        max_videos = self.max_videos_input.value()
        delay_between_videos = self.delay_input.value()
        
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.append_log(f"Bắt đầu xử lý kênh: {channel_url}")
        self.append_log(f"Cài đặt: Số lượng video tối đa={max_videos}, Thời gian chờ={delay_between_videos}s")
        
        self.worker_thread = threading.Thread(
            target=self.run_automation,
            args=(channel_url, max_videos, delay_between_videos)
        )
        self.worker_thread.daemon = True
        self.worker_thread.start()
    
    def run_automation(self, channel_url, max_videos, delay_between_videos):
        try:
            # Lấy mẫu bình luận từ giao diện (dạng multi-line text)
            templates = self.get_comment_templates()
            automator = YouTubeAutomator(self.worker_signals, comment_templates=templates)
            automator.process_channel(
                channel_url=channel_url,
                max_videos=max_videos,
                delay_between_videos=delay_between_videos
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
