import os
from dotenv import load_dotenv
from seleniumbase import SB
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

load_dotenv()
data_url = os.getenv("DATA_URL")

def scrape_anaslo_corrected():
    with SB(uc=True, headless=False) as sb:
        target_url = data_url

        try: 
            print("1. 対象サイトへアクセスします...")
            # Cloudflareを通過するための専用メソッド
            sb.uc_open_with_reconnect(target_url, reconnect_time=5)
            
            # 「人間であることを確認します」のチェックボックスがあれば自動クリック
            sb.uc_gui_click_captcha()

            # 2. data_table が読み込まれるまで待機 (最大15秒)
            # SeleniumBaseの強力な待機メソッドを使用
            sb.wait_for_element(".date-list-area", timeout=15)
            
            # 3. テーブル内の最初のaタグのhref属性を取得
            latest_link_url = sb.get_attribute(".table-data-cell a", "href")
            print(f"✅ 最新日のリンクを取得しました: {latest_link_url}")

            # サーバー負荷対策の待機
            time.sleep(3)

            print("2. 最新日のページへ遷移します...")
            # 4. 最新日のリンクへ遷移し、再度セキュリティ検証を突破
            sb.uc_open_with_reconnect(latest_link_url, reconnect_time=5)
            sb.uc_gui_click_captcha()

            # ページの主要要素(body)が読み込まれるまで待機
            sb.wait_for_element("body", timeout=15)
            time.sleep(3) # 動的レンダリング待ち

            # 5. BeautifulSoupに渡してスクレイピング
            html_content = sb.get_page_source()
            soup = BeautifulSoup(html_content, 'html.parser')
            
            print("✅ ページの取得に成功しました！")
            print("タイトル:", soup.title.text)
            
            # 以降、soupを使って必要なデータを抽出してください
            # 例: data = soup.find(...)

        except Exception as e:
            print(f"❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    scrape_anaslo_corrected()