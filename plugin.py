import requests
import zipfile
import io
import os
import subprocess
import json
from datetime import datetime

# ——— CẤU HÌNH ———
API_URL = (
    "https://api.wordpress.org/plugins/info/1.2/"
    "?action=query_plugins"
    "&request[browse]=popular"
    "&request[per_page]=1000"
)
# Đường dẫn đến thư mục gốc WordPress local của bạn
WP_PATH = r"C:/laragon/www/test"
# Số lượng plugin phổ biến muốn cài
NUM_TO_INSTALL = 50
# Nếu bạn chỉ muốn tải mà không activate, để False
ACTIVATE_PLUGINS = True

# Thư mục plugins và báo cáo
PLUGINS_DIR = os.path.join(WP_PATH, "wp-content", "plugins")
REPORT_DIR = os.path.join(WP_PATH, "reports")
# Tạo thư mục nếu chưa tồn tại
os.makedirs(PLUGINS_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


def get_popular_plugins():
    """Gọi API và trả về list các dict plugin chứa thông tin."""
    resp = requests.get(API_URL)
    resp.raise_for_status()
    data = resp.json()
    return data.get("plugins", [])


def download_and_extract_plugin(plugin: dict):
    """Tải zip của plugin (dùng download_link từ API) và giải nén vào wp-content/plugins."""
    download_url = plugin.get("download_link")
    slug = plugin.get("slug")
    resp = requests.get(download_url)
    resp.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        print(f"→ Giải nén plugin {slug} vào {PLUGINS_DIR}")
        z.extractall(PLUGINS_DIR)


def activate_plugin(plugin: dict):
    """Kích hoạt plugin bằng WP-CLI."""
    slug = plugin.get("slug")
    print(f"→ Kích hoạt plugin: {slug}")
    subprocess.run(
        ["wp", "plugin", "activate", slug],
        cwd=WP_PATH,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def main():
    # Bước 1: Lấy danh sách các plugin phổ biến
    plugins = get_popular_plugins()[:NUM_TO_INSTALL]
    total = len(plugins)
    print(f"Sẽ xử lý {total} plugin phổ biến.")

    report = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "plugins": []
    }

    # Bước 2: Tải & giải nén, sau đó kích hoạt nếu cần
    for idx, plugin in enumerate(plugins, start=1):
        slug = plugin.get("slug")
        print(f"\n=== [{idx}/{total}] XỬ LÝ PLUGIN: {slug} ===")
        plugin_path = os.path.join(PLUGINS_DIR, slug)

        # Kiểm tra tồn tại
        if os.path.isdir(plugin_path):
            status = "skipped_exists"
            print(f"→ Bỏ qua {slug}, đã tồn tại.")
        else:
            try:
                download_and_extract_plugin(plugin)
                status = "downloaded"
                if ACTIVATE_PLUGINS:
                    activate_plugin(plugin)
                    status = "activated"
            except Exception as e:
                status = f"error: {e}"
                print(f"→ Lỗi khi xử lý {slug}: {e}")

        report["plugins"].append({
            "slug": slug,
            "status": status
        })

    # Ghi báo cáo ra file JSON
    report_file = os.path.join(
        REPORT_DIR,
        f"plugin_install_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\nHoàn tất! Báo cáo lưu tại: {report_file}")


if __name__ == "__main__":
    main()