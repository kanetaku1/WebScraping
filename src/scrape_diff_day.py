import os
import re
import time
import random
import urllib.parse
from dotenv import load_dotenv
from seleniumbase import SB
from bs4 import BeautifulSoup

load_dotenv()
data_url = os.getenv("DATA_URL")

def sanitize_filename(filename):
    """ファイル名として使えない記号を置換する関数"""
    filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
    filename = filename.replace('\n', '').replace('\r', '').replace('/', '-').strip()
    return filename

def scrape_anaslo_incremental():
    save_dir = "data"
    os.makedirs(save_dir, exist_ok=True)
    print(f"📂 保存先ディレクトリを確認: {save_dir}/")

    with SB(uc=True, headless=False) as sb:
        target_url = data_url

        try: 
            print("1. 対象サイトへアクセスし、リンク一覧を取得します...")
            sb.uc_open_with_reconnect(target_url, reconnect_time=5)
            sb.uc_gui_click_captcha()

            sb.wait_for_element(".date-list-area", timeout=15)
            
            list_page_html = sb.get_page_source()
            list_soup = BeautifulSoup(list_page_html, 'html.parser')
            link_elements = list_soup.select(".table-data-cell a")
            
            # --- 差分チェック用リストの準備 ---
            all_links_count = len(link_elements)
            new_targets = [] # 新規で取得すべきリンクだけを格納するリスト

            for a in link_elements:
                href = a.get("href")
                if href:
                    date_text = a.text.strip()
                    if not date_text:
                        date_text = urllib.parse.unquote(href.rstrip('/').split('/')[-1])
                    
                    filename = sanitize_filename(date_text)
                    filepath = os.path.join(save_dir, f"{filename}.html")
                    
                    # 【重要】手元のフォルダにファイルが存在しない場合のみ、新規取得リストに追加
                    if not os.path.exists(filepath):
                        new_targets.append({
                            "url": href, 
                            "filename": filename,
                            "filepath": filepath
                        })

            print(f"✅ サイト上の全データ数: {all_links_count} 件")
            print(f"🆕 新規取得が必要なデータ数: {len(new_targets)} 件\n")

            # 新しく取得するデータがなければ、ここで即座にプログラムを終了
            if len(new_targets) == 0:
                print("🎉 すべてのデータが最新です！新しく取得する日付はありません。")
                return 

            time.sleep(3)

            # --- 新しいデータのみをループして取得 ---
            for index, target in enumerate(new_targets, 1):
                url = target["url"]
                filepath = target["filepath"]
                filename = target["filename"]
                
                print(f"[{index}/{len(new_targets)}] 新規取得中: {filename}")
                
                sb.uc_open_with_reconnect(url, reconnect_time=5)
                sb.uc_gui_click_captcha()

                sb.wait_for_element("body", timeout=15)
                
                # サーバー負荷対策のランダム待機
                wait_time = random.uniform(3.0, 5.0)
                time.sleep(wait_time) 

                html_content = sb.get_page_source()
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(html_content)
                
                print(f"  ✅ 保存完了: {filepath}")

            print("\n🎉 新規データの取得・保存がすべて完了しました！")

        except Exception as e:
            print(f"\n❌ エラーが発生しました: {e}")

if __name__ == "__main__":
    scrape_anaslo_incremental()