import sys
import time
import random
import threading
import json
import os
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QSpinBox, QProgressBar, QTextEdit, QFrame, QTabWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QFont, QIcon, QColor

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

class WorkerSignals(QObject):
    """Define signals for worker thread communication"""
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal()
    history_update = pyqtSignal(dict)

class YouTubeAutomator:
    def __init__(self, signals):
        """Initialize YouTube automation with signals for UI updates"""
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
        
        # Comment templates
        self.comment_templates = [
            "Video rất hay, cảm ơn bạn đã chia sẻ!",
            "Nội dung tuyệt vời, tôi đã học được nhiều điều!",
            "Chất lượng video rất tốt, mong chờ các video tiếp theo!",
            "Cảm ơn vì nội dung hữu ích!",
            "Tôi thích video này, đã đăng ký kênh của bạn!"
        ]
    
    def get_channel_videos(self, channel_url):
        """Get list of video URLs from a channel"""
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
        
        # Also get video titles for history
        video_titles = [elem.get_attribute('title') for elem in video_elements if elem.get_attribute('href')]
        
        video_info = list(zip(video_urls, video_titles))
        self.signals.log.emit(f"Found {len(video_info)} videos from channel")
        return video_info
    
    def like_and_comment(self, video_url, video_title):
        """Open video, like and comment"""
        self.signals.log.emit(f"Opening video: {video_url}")
        self.signals.log.emit(f"Title: {video_title}")
        self.driver.get(video_url)
        
        result = {
            "url": video_url,
            "title": video_title,
            "liked": False,
            "commented": False,
            "comment_text": "",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            # Wait for video to load
            time.sleep(5)
            
            # Like video
            try:
                like_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Thích' or @aria-label='Like']")))
                like_button.click()
                self.signals.log.emit("✅ Liked video")
                result["liked"] = True
                time.sleep(1)
            except (TimeoutException, NoSuchElementException):
                self.signals.log.emit("⚠️ Like button not found")
            
            # Comment
            try:
                # Scroll to comment section
                self.driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(2)
                
                # Find and click comment box
                comment_box = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#simplebox-placeholder")))
                comment_box.click()
                time.sleep(1)
                
                # Enter comment
                comment_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#contenteditable-root")))
                random_comment = random.choice(self.comment_templates)
                comment_input.send_keys(random_comment)
                result["comment_text"] = random_comment
                time.sleep(1)
                
                # Submit comment
                submit_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#submit-button")))
                submit_button.click()
                self.signals.log.emit(f"✅ Posted comment: '{random_comment}'")
                result["commented"] = True
                time.sleep(2)
                
                # Return video interaction result for history
                self.signals.history_update.emit(result)
                return True
            except (TimeoutException, NoSuchElementException) as e:
                self.signals.log.emit(f"⚠️ Error commenting: {e}")
                self.signals.history_update.emit(result)
                return False
            
        except Exception as e:
            self.signals.log.emit(f"❌ Error processing video {video_url}: {e}")
            self.signals.history_update.emit(result)
            return False
    
    def process_channel(self, channel_url, max_videos=None, delay_between_videos=30):
        """Process entire channel: open each video, like and comment"""
        # Initialize session history
        session_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session_history = {
            "channel_url": channel_url,
            "start_time": session_start,
            "videos": []
        }
        
        # Get video list
        try:
            video_info = self.get_channel_videos(channel_url)
            
            # Extract channel name if possible
            try:
                channel_name = self.driver.find_element(By.ID, "channel-name").text
                session_history["channel_name"] = channel_name
                self.signals.log.emit(f"Channel name: {channel_name}")
            except:
                session_history["channel_name"] = "Unknown Channel"
            
            # Limit number of videos if needed
            if max_videos and max_videos < len(video_info):
                video_info = video_info[:max_videos]
                self.signals.log.emit(f"Limited to first {max_videos} videos")
            
            # Process each video
            for i, (url, title) in enumerate(video_info):
                self.signals.log.emit(f"\n📺 Processing video {i+1}/{len(video_info)}")
                success = self.like_and_comment(url, title)
                
                # Update progress
                progress_percent = int((i + 1) / len(video_info) * 100)
                self.signals.progress.emit(progress_percent)
                
                # Wait between videos to avoid detection as bot
                if i < len(video_info) - 1 and success:  # Don't wait after last video
                    self.signals.log.emit(f"⏱️ Waiting {delay_between_videos} seconds before next video...")
                    time.sleep(delay_between_videos)
            
            # Complete session history
            session_history["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            session_history["videos_processed"] = len(video_info)
            
            self.signals.log.emit("\n✅ All videos processed successfully!")
            self.signals.progress.emit(100)
            self.signals.finished.emit()
            
        except Exception as e:
            self.signals.log.emit(f"❌ Error: {e}")
            session_history["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            session_history["error"] = str(e)
            self.signals.finished.emit()

class HistoryManager:
    """Manage processing history"""
    def __init__(self):
        self.history_file = "youtube_automator_history.json"
        self.history = self.load_history()
        
    def load_history(self):
        """Load history from file or create new if doesn't exist"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as file:
                    return json.load(file)
            except:
                return {"sessions": [], "videos": []}
        else:
            return {"sessions": [], "videos": []}
    
    def save_history(self):
        """Save history to file"""
        with open(self.history_file, 'w', encoding='utf-8') as file:
            json.dump(self.history, file, ensure_ascii=False, indent=2)
    
    def add_video_interaction(self, video_data):
        """Add a video interaction to history"""
        self.history["videos"].append(video_data)
        self.save_history()
    
    def add_session(self, session_data):
        """Add a complete session to history"""
        self.history["sessions"].append(session_data)
        self.save_history()
    
    def get_history(self):
        """Return full history"""
        return self.history

class YouTubeAutomationUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Channel Automator")
        self.setMinimumSize(800, 600)
        
        # Initialize worker thread variables
        self.worker_thread = None
        self.worker_signals = WorkerSignals()
        
        # Connect signals
        self.worker_signals.progress.connect(self.update_progress)
        self.worker_signals.log.connect(self.append_log)
        self.worker_signals.finished.connect(self.on_process_finished)
        self.worker_signals.history_update.connect(self.update_history)
        
        # Initialize history manager BEFORE initUI
        self.history_manager = HistoryManager()
        
        # Now initialize the UI
        self.initUI()
    
    def initUI(self):
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Title
        title_label = QLabel("YouTube Channel Automator")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont("Arial", 18, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #FF0000; margin: 10px;")
        main_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Automatically like and comment on videos from a YouTube channel")
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("color: #555; font-size: 14px; margin-bottom: 20px;")
        main_layout.addWidget(desc_label)
        
        # Tab widget for main content
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Main tab
        main_tab = QWidget()
        main_tab_layout = QVBoxLayout()
        main_tab.setLayout(main_tab_layout)
        
        # Input form
        form_container = QWidget()
        form_container.setStyleSheet("background-color: #f5f5f5; border-radius: 10px; padding: 20px;")
        form_layout = QVBoxLayout()
        form_container.setLayout(form_layout)
        
        # Channel URL input
        url_layout = QHBoxLayout()
        url_label = QLabel("Channel URL:")
        url_label.setMinimumWidth(120)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/@channelname")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        form_layout.addLayout(url_layout)
        
        # Settings layout
        settings_layout = QHBoxLayout()
        
        # Max videos
        max_videos_layout = QHBoxLayout()
        max_videos_label = QLabel("Max Videos:")
        self.max_videos_input = QSpinBox()
        self.max_videos_input.setRange(1, 100)
        self.max_videos_input.setValue(10)
        max_videos_layout.addWidget(max_videos_label)
        max_videos_layout.addWidget(self.max_videos_input)
        settings_layout.addLayout(max_videos_layout)
        
        # Delay between videos
        delay_layout = QHBoxLayout()
        delay_label = QLabel("Delay (seconds):")
        self.delay_input = QSpinBox()
        self.delay_input.setRange(10, 300)
        self.delay_input.setValue(30)
        delay_layout.addWidget(delay_label)
        delay_layout.addWidget(self.delay_input)
        settings_layout.addLayout(delay_layout)
        
        form_layout.addLayout(settings_layout)
        
        # Buttons
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
        
        # Progress
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
        
        # Log section
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
        
        # Add main tab
        self.tab_widget.addTab(main_tab, "Process")
        
        # History tab
        history_tab = QWidget()
        history_layout = QVBoxLayout()
        history_tab.setLayout(history_layout)
        
        # History section
        history_label = QLabel("Processing History:")
        history_label.setFont(QFont("Arial", 12, QFont.Bold))
        history_layout.addWidget(history_label)
        
        self.history_text = QTextEdit()
        self.history_text.setReadOnly(True)
        self.history_text.setStyleSheet("background-color: #f9f9f9; border: 1px solid #ddd; border-radius: 5px;")
        history_layout.addWidget(self.history_text)
        
        # Refresh history button
        refresh_button = QPushButton("Refresh History")
        refresh_button.clicked.connect(self.display_history)
        history_layout.addWidget(refresh_button)
        
        # Add history tab
        self.tab_widget.addTab(history_tab, "History")
        
        # Footer with copyright
        footer_label = QLabel()
        footer_label.setText('Copyright by toanAI- <a href="http://doxuantoan.com">doxuantoandotcom</a>')
        footer_label.setOpenExternalLinks(True)
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("color: #555; margin-top: 10px;")
        main_layout.addWidget(footer_label)
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Load and display history
        self.display_history()
    
    def display_history(self):
        """Display processing history in the history tab"""
        history_data = self.history_manager.get_history()
        
        # Clear existing content
        self.history_text.clear()
        
        if not history_data["videos"]:
            self.history_text.append("No history available yet.")
            return
        
        # Sort videos by timestamp (newest first)
        sorted_videos = sorted(
            history_data["videos"], 
            key=lambda x: datetime.strptime(x.get("timestamp", "2000-01-01 00:00:00"), "%Y-%m-%d %H:%M:%S"),
            reverse=True
        )
        
        # Display history
        self.history_text.append("### Recent Activity ###\n")
        
        for i, video in enumerate(sorted_videos[:50]):  # Limit to 50 most recent entries
            self.history_text.append(f"Entry #{i+1} - {video.get('timestamp', 'Unknown time')}")
            self.history_text.append(f"Title: {video.get('title', 'Unknown title')}")
            self.history_text.append(f"URL: {video.get('url', 'Unknown URL')}")
            self.history_text.append(f"Liked: {'✅' if video.get('liked', False) else '❌'}")
            self.history_text.append(f"Commented: {'✅' if video.get('commented', False) else '❌'}")
            if video.get('commented', False):
                self.history_text.append(f"Comment: \"{video.get('comment_text', '')}\"")
            self.history_text.append("-" * 50 + "\n")
    
    def append_log(self, message):
        """Add a message to the log with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_text.append(formatted_message)
        # Auto scroll to bottom
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())
    
    def update_progress(self, value):
        """Update progress bar value"""
        self.progress_bar.setValue(value)
        self.statusBar().showMessage(f"Progress: {value}%")
    
    def update_history(self, video_data):
        """Update history with new video interaction"""
        self.history_manager.add_video_interaction(video_data)
    
    def start_process(self):
        """Start the automation process in a separate thread"""
        # Validate inputs
        channel_url = self.url_input.text().strip()
        if not channel_url:
            self.append_log("❌ Please enter a valid channel URL")
            return
        
        if not (channel_url.startswith("https://www.youtube.com/") or 
                channel_url.startswith("https://youtube.com/")):
            self.append_log("❌ Invalid YouTube URL format")
            return
        
        # Get settings
        max_videos = self.max_videos_input.value()
        delay_between_videos = self.delay_input.value()
        
        # Update UI state
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setValue(0)
        self.append_log(f"Starting process for channel: {channel_url}")
        self.append_log(f"Settings: Max Videos={max_videos}, Delay={delay_between_videos}s")
        
        # Record session start in history
        session_start = {
            "channel_url": channel_url,
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "max_videos": max_videos,
            "delay": delay_between_videos,
            "status": "running"
        }
        self.history_manager.add_session(session_start)
        
        # Start worker thread
        self.worker_thread = threading.Thread(
            target=self.run_automation,
            args=(channel_url, max_videos, delay_between_videos)
        )
        self.worker_thread.daemon = True
        self.worker_thread.start()
    
    def run_automation(self, channel_url, max_videos, delay_between_videos):
        """Run the automation process (called from worker thread)"""
        try:
            automator = YouTubeAutomator(self.worker_signals)
            automator.process_channel(
                channel_url=channel_url,
                max_videos=max_videos,
                delay_between_videos=delay_between_videos
            )
        except Exception as e:
            self.worker_signals.log.emit(f"❌ Critical error: {e}")
            self.worker_signals.finished.emit()
    
    def stop_process(self):
        """Stop the current process"""
        if self.worker_thread and self.worker_thread.is_alive():
            self.append_log("🛑 Stopping process... (may take a moment)")
            # We can't directly stop the thread, but we'll change the UI state
            # The thread will terminate when it finishes its current operation
            self.on_process_finished()
    
    def on_process_finished(self):
        """Handle process completion (called when worker thread finishes)"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.statusBar().showMessage("Ready")
        
        # Update history display
        self.display_history()
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.worker_thread and self.worker_thread.is_alive():
            # If thread is running, try to clean up
            self.append_log("Closing application...")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set app style
    app.setStyle("Fusion")
    
    window = YouTubeAutomationUI()
    window.show()
    
    sys.exit(app.exec_())