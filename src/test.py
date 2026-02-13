import pandas as pd
import numpy as np
from scipy import stats
import re
import os
import io  # 追加
from bs4 import BeautifulSoup

class JugglerAnalyzer:
    def __init__(self):
        self.specs = {
            1: (1/273.1, 1/439.8), 2: (1/269.7, 1/439.8), 3: (1/269.7, 1/341.3),
            4: (1/259.0, 1/315.1), 5: (1/259.0, 1/255.0), 6: (1/255.0, 1/255.0)
        }

    def calculate_p56(self, g, bb, rb):
        if pd.isna(g) or g < 3000: return np.nan
        priors = {s: 1/6 for s in range(1, 7)}
        weighted_l = []
        for s in range(1, 7):
            p_bb, p_rb = self.specs[s]
            l = stats.binom.pmf(bb, g, p_bb) * stats.binom.pmf(rb, g, p_rb)
            weighted_l.append(l * priors[s])
        total_l = sum(weighted_l)
        return (weighted_l[4] + weighted_l[5]) / total_l if total_l > 0 else 0.0

    def process_html(self, file_path):
        print(f"\n--- 処理開始: {os.path.basename(file_path)} ---")
        try:
            # BOM付きUTF-8への対応を強化
            with open(file_path, 'r', encoding='utf-8-sig', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"ファイル読み込みエラー: {e}")
            return None

        soup = BeautifulSoup(content, 'html.parser')
        target_h4 = soup.find(lambda tag: tag.name == 'h4' and 'ネオアイムジャグラーEX' in tag.text)
        
        if not target_h4:
            print("見出し『ネオアイムジャグラーEX』が見つかりませんでした。")
            return None

        target_table = target_h4.find_next('table')
        if not target_table:
            print("見出しの後にテーブルが見つかりませんでした。")
            return None

        # 修正ポイント：io.StringIO で包むことで、文字列をファイルとして誤認させない
        try:
            table_html = str(target_table)
            df = pd.read_html(io.StringIO(table_html), flavor='html5lib')[0]
            print("テーブルの読み込みに成功しました。")
        except Exception as e:
            print(f"テーブル解析エラー: {e}")
            return None

        # データクレンジング
        # 台番号が数値でない行（平均行など）を確実に除外
        df = df[df['台番号'].astype(str).str.contains(r'\d')].copy()
        
        for col in ['台番号', 'G数', 'BB', 'RB']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(r'[^\d]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        # 日付と特日判定
        date_match = re.search(r'(\d{4})_(\d{2})_(\d{2})', os.path.basename(file_path))
        date_str = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}" if date_match else "unknown"
        day = int(date_match.group(3)) if date_match else 0
        
        df['date'] = date_str
        df['is_special'] = 1 if day in [7, 17, 27] else 0
        
        # 設定5・6確率の計算
        df['prob_56'] = df.apply(lambda r: self.calculate_p56(r['G数'], r['BB'], r['RB']), axis=1)

        print(f"解析完了: {len(df)}台のデータを取得しました。")
        return df[['date', 'is_special', '台番号', 'G数', 'BB', 'RB', 'prob_56']]

if __name__ == "__main__":
    analyzer = JugglerAnalyzer()
    # 適切なパスに変更してください
    file_path = r'c:/WorkSpace/Python/Scraping/2026_02_11.html'
    
    result = analyzer.process_html(file_path)
    if result is not None:
        output_file = 'juggler_analysis_result.csv'
        result.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"CSVを書き出しました: {os.path.abspath(output_file)}")
        # 上位結果を少し表示
        print("\n--- 推定設定5・6確率が高い台 ---")
        print(result.dropna(subset=['prob_56']).sort_values('prob_56', ascending=False).head())
    else:
        print("CSVは作成されませんでした。")