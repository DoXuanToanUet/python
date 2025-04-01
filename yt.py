import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

class YouTubeAutomator:
    def __init__(self):
        """Kết nối với trình duyệt Chrome đang chạy"""
        options = Options()
        options.add_experimental_option("debuggerAddress", "localhost:9222")
        
        self.driver = webdriver.Chrome(options=options)
        self.wait = WebDriverWait(self.driver, 10)
        
        # Danh sách comment mẫu để lựa chọn ngẫu nhiên
        self.comment_templates = [
            "Video rất hay, cảm ơn bạn đã chia sẻ!",
            "Nội dung tuyệt vời, tôi đã học được nhiều điều!",
            "Chất lượng video rất tốt, mong chờ các video tiếp theo!",
            "Cảm ơn vì nội dung hữu ích!",
            "Tôi thích video này, đã đăng ký kênh của bạn!"
        ]
    
    # Không cần phương thức login_to_youtube nữa vì bạn đã đăng nhập trên Chrome hiện tại
    
    def get_channel_videos(self, channel_url):
        """Lấy danh sách URL của tất cả video trong kênh"""
        # Chuyển đến tab Videos của kênh
        videos_url = channel_url + "/videos"
        self.driver.get(videos_url)
        time.sleep(3)
        
        # Cuộn trang để tải thêm video
        for _ in range(5):  # Cuộn 5 lần để lấy nhiều video
            self.driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(2)
        
        # Lấy tất cả các link video
        video_elements = self.driver.find_elements(By.CSS_SELECTOR, "a#video-title-link")
        video_urls = [elem.get_attribute('href') for elem in video_elements if elem.get_attribute('href')]
        
        print(f"Đã tìm thấy {len(video_urls)} video từ kênh.")
        return video_urls
    
    def like_and_comment(self, video_url):
        """Mở video, like và comment"""
        self.driver.get(video_url)
        
        try:
            # Chờ video tải
            time.sleep(5)
            
            # Like video
            try:
                like_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".ytLikeButtonViewModelHost")))
                like_button.click()
                print("Đã like video.")
                time.sleep(1)
            except (TimeoutException, NoSuchElementException):
                print("Không thể tìm thấy nút like.")
            
            # Comment
            try:
                # Cuộn xuống phần comment
                self.driver.execute_script("window.scrollBy(0, 500);")
                time.sleep(2)
                
                # Tìm và click vào ô comment
                comment_box = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#simplebox-placeholder")))
                comment_box.click()
                time.sleep(1)
                
                # Nhập comment
                comment_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#contenteditable-root")))
                random_comment = random.choice(self.comment_templates)
                comment_input.send_keys(random_comment)
                time.sleep(1)
                
                # Gửi comment
                submit_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#submit-button")))
                submit_button.click()
                print(f"Đã comment: '{random_comment}'")
                time.sleep(2)
            except (TimeoutException, NoSuchElementException) as e:
                print(f"Lỗi khi comment: {e}")
            
        except Exception as e:
            print(f"Lỗi khi xử lý video {video_url}: {e}")
    
    def process_channel(self, channel_url, max_videos=None, delay_between_videos=30):
        """Xử lý toàn bộ kênh: mở từng video, like và comment"""
        # Lấy danh sách video
        video_urls = self.get_channel_videos(channel_url)
        
        # Giới hạn số lượng video nếu cần
        if max_videos and max_videos < len(video_urls):
            video_urls = video_urls[:max_videos]
        
        # Xử lý từng video
        for i, url in enumerate(video_urls):
            print(f"\nXử lý video {i+1}/{len(video_urls)}: {url}")
            self.like_and_comment(url)
            
            # Chờ giữa các video để tránh bị phát hiện là bot
            if i < len(video_urls) - 1:  # Không chờ sau video cuối cùng
                print(f"Chờ {delay_between_videos} giây trước khi xử lý video tiếp theo...")
                time.sleep(delay_between_videos)
        
        print("\nHoàn thành tất cả video!")

# Ví dụ sử dụng
if __name__ == "__main__":
    # Thông số đầu vào
    channel_url = "https://www.youtube.com/@toanyoutuber6376/videos"  # Thay thế bằng URL kênh thực tế
    
    bot = YouTubeAutomator()
    
    try:
        bot.process_channel(
            channel_url=channel_url,
            max_videos=1,  # Giới hạn số video xử lý
            delay_between_videos=30  # Thời gian chờ giữa các video (giây)
        )
    except Exception as e:
        print(f"Lỗi: {e}")