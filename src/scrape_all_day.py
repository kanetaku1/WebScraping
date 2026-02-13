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
    """ファイル名として使えない記号をアンダースコアに置換する関数"""
    filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
    # スラッシュや改行なども削除・置換
    filename = filename.replace('\n', '').replace('\r', '').replace('/', '-').strip()
    return filename

def scrape_anaslo_all_data():
    # 1. 保存先ディレクトリ（data/）の作成
    save_dir = "data"
    os.makedirs(save_dir, exist_ok=True)
    print(f"📂 保存先ディレクトリを準備しました: {save_dir}/")

    with SB(uc=True, headless=False) as sb:
        target_url = data_url

        try: 
            print("1. 対象サイトへアクセスし、リンク一覧を取得します...")
            sb.uc_open_with_reconnect(target_url, reconnect_time=5)
            sb.uc_gui_click_captcha()

            sb.wait_for_element(".date-list-area", timeout=15)
            
            # --- 追加: BeautifulSoupで一覧ページの全リンクを取得 ---
            list_page_html = sb.get_page_source()
            list_soup = BeautifulSoup(list_page_html, 'html.parser')
            link_elements = list_soup.select(".table-data-cell a")
            
            # リンクURLと、ファイル名にするためのテキスト（日付）をリストに格納
            targets = []
            for a in link_elements:
                href = a.get("href")
                if href:
                    # リンクのテキスト（例: "10月1日"）を取得
                    date_text = a.text.strip()
                    # もしテキストが取れなかった場合は、URLの末尾をファイル名代わりにする
                    if not date_text:
                        date_text = urllib.parse.unquote(href.rstrip('/').split('/')[-1])
                    
                    filename = sanitize_filename(date_text)
                    if not filename:
                        filename = f"page_{len(targets)}"
                        
                    targets.append({"url": href, "filename": filename})

            total_pages = len(targets)
            print(f"✅ 合計 {total_pages} 件のデータリンクを取得しました。\n")
            time.sleep(3)

            # --- 追加: 取得した全リンクに対してループ処理 ---
            for index, target in enumerate(targets, 1):
                url = target["url"]
                base_filename = target["filename"]
                filepath = os.path.join(save_dir, f"{base_filename}.html")
                
                print(f"[{index}/{total_pages}] 対象: {base_filename}")
                
                # すでにファイルが存在する場合はスキップ（再実行時の時短）
                if os.path.exists(filepath):
                    print(f"  ⏭️ すでに保存されているためスキップします。")
                    continue

                # ページへ遷移し、セキュリティ検証を突破
                sb.uc_open_with_reconnect(url, reconnect_time=5)
                sb.uc_gui_click_captcha()

                # 主要要素が読み込まれるまで待機
                sb.wait_for_element("body", timeout=15)
                
                # 動的レンダリング待ち 兼 サーバー負荷対策の待機 (3秒〜6秒のランダム)
                wait_time = random.uniform(3.0, 6.0)
                time.sleep(wait_time) 

                # ページソースを取得して保存
                html_content = sb.get_page_source()
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(html_content)
                
                print(f"  ✅ 保存完了: {filepath}")

            print("\n🎉 すべてのデータ取得・保存が完了しました！")

        except Exception as e:
            print(f"\n❌ エラーが発生しました: {e}")
            print("💡 途中でエラーが起きても、次回実行時は保存済みの分はスキップされます。")

if __name__ == "__main__":
    scrape_anaslo_all_data()