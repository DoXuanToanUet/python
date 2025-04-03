import sys
import time
import random
import threading
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

class YouTubeAutomator:
    def __init__(self, signals, comment_templates=None):
        """Khởi tạo tự động hóa YouTube với các tín hiệu giao tiếp và mẫu bình luận.
           Nếu truyền vào comment_templates (dạng đoạn văn đa dòng), sẽ tách theo dòng."""
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
            # Tách từng dòng thành một mẫu bình luận, bỏ qua dòng trống
            self.comment_templates = [line.strip() for line in comment_templates.splitlines() if line.strip()]
        else:
            # Mẫu bình luận mặc định
            self.comment_templates = [
                "Video rất hay, cảm ơn bạn đã chia sẻ!",
                "Nội dung tuyệt vời, tôi đã học được nhiều điều!",
                "Chất lượng video rất tốt, mong chờ các video tiếp theo!",
                "Cảm ơn vì nội dung hữu ích!",
                "Tôi thích video này, đã đăng ký kênh của bạn!"
            ]
    
    def get_channel_videos(self, channel_url):
        """Lấy danh sách URL video của kênh"""
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
    
    def like_and_comment(self, video_url, video_title, session_id):
        """Mở video, thực hiện like và bình luận"""
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
            # Thực hiện like video
            try:
                like_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".ytLikeButtonViewModelHost")))
                like_button.click()
                self.signals.log.emit("✅ Liked video")
                result["liked"] = True
                time.sleep(1)
            except (TimeoutException, NoSuchElementException):
                self.signals.log.emit("⚠️ Like button not found")
            
            # Thực hiện bình luận
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
                
                self.signals.history_update.emit(result)
                return result
            except (TimeoutException, NoSuchElementException) as e:
                self.signals.log.emit(f"⚠️ Error commenting: {e}")
                self.signals.history_update.emit(result)
                return result
            
        except Exception as e:
            self.signals.log.emit(f"❌ Error processing video {video_url}: {e}")
            self.signals.history_update.emit(result)
            return result
    
    def process_channel(self, channel_url, max_videos=None, delay_between_videos=30):
        """Xử lý toàn bộ kênh: duyệt từng video, like và bình luận"""
        session_id = f"session_{int(time.time())}"
        session_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session_history = {
            "session_id": session_id,
            "channel_url": channel_url,
            "start_time": session_start,
            "videos": []
        }
        
        self.signals.session_update.emit(session_history)
        
        try:
            video_info = self.get_channel_videos(channel_url)
            
            try:
                channel_name = self.driver.find_element(By.ID, "channel-name").text
                session_history["channel_name"] = channel_name
                self.signals.log.emit(f"Channel name: {channel_name}")
            except:
                session_history["channel_name"] = "Unknown Channel"
            
            if max_videos and max_videos < len(video_info):
                video_info = video_info[:max_videos]
                self.signals.log.emit(f"Limited to first {max_videos} videos")
            
            processed_videos = []
            for i, (url, title) in enumerate(video_info):
                self.signals.log.emit(f"\n📺 Processing video {i+1}/{len(video_info)}")
                video_result = self.like_and_comment(url, title, session_id)
                processed_videos.append(video_result)
                session_history["videos"].append(url)
                progress_percent = int((i + 1) / len(video_info) * 100)
                self.signals.progress.emit(progress_percent)
                
                if i < len(video_info) - 1:
                    self.signals.log.emit(f"⏱️ Waiting {delay_between_videos} seconds before next video...")
                    time.sleep(delay_between_videos)
            
            session_history["end_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            session_history["videos_processed"] = len(video_info)
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