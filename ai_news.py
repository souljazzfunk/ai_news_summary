import requests
from google import genai
import re
import time
import os
from datetime import datetime
import pytz
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def fetch_latest_article(url, last_date_file="last_date.txt"):
    """
    Fetch the latest article from Buttondown archive page.
    Only returns content if the article date has changed since the last fetch.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the first article with non-empty metadata
        article = None
        for a_tag in soup.find_all('a'):
            metadata_div = a_tag.find('div', class_='email-metadata')
            if metadata_div and metadata_div.text.strip():
                article = a_tag
                break

        if not article:
            print("No article found with metadata")
            return None

        # Extract date and URL
        article_date = article.find('div', class_='email-metadata').text.strip()
        article_url = article['href']

        print("出典： " + article_url)
        print("更新： " + article_date)
        print()

        # Load last date from file, if it exists
        try:
            with open(last_date_file, "r") as f:
                previous_date = f.read().strip()
        except FileNotFoundError:
            previous_date = None

        # Compare dates
        if article_date == previous_date:
            print("No new article found. Exiting.")
            return None

        # If updated, save the new date
        with open(last_date_file, "w") as f:
            f.write(article_date)

        # Fetch article content
        article_response = requests.get(article_url)
        article_response.raise_for_status()
        return article_response.text

    except requests.RequestException as e:
        print(f"Error fetching content: {e}")
        return None


def analyze_with_gemini(xml_content, api_key, model):
    """Analyze XML content using Gemini model"""
    client = genai.Client(api_key=api_key)

    prompt = """
以下のXML形式のコンテンツを分析し、以下の手順に従って記事の要約を作成してください。

1. XMLコンテンツから、注目すべきトピックの上位10件を選定、抽出してください。
    - ただし、トップニュースがおもしろいとは限りません

2. 抽出した各トピックを以下の形式で記述してください。
    - トピックの見出し
    - 約100字程度の要約
    - 選定したトピックのソースURL（必ず1件）
    - ニュースの注目点を約400字程度にまとめた解説

3. 上記の内容を、日本の読者が読みやすい自然な日本語に翻訳してください。
    - open-weightのモデルのことは「オープンウェイトモデル」と訳してください。
    - 「オープンソース」という用語はできるだけ避け、「オープンウェイト」または「寛容なライセンスの」と訳してください。
    - The open-source definition, as outlined by the Open Source Initiative (OSI):
        1. **Free Redistribution**: The software must be freely redistributable, allowing anyone to give away or sell the software without restrictions[8].
        2. **Source Code**: The source code must be included with the software or easily obtainable, allowing users to modify it[8].
        3. **Derived Works**: Users must be allowed to modify the software and distribute their modifications under the same terms as the original software[8].
        4. **Integrity of The Author's Source Code**: The license may restrict source code modifications, but it must allow distribution of patches along with the source code for the purpose of modifying it[8].
        5. **No Discrimination Against Persons or Groups**: The license must not discriminate against any person or group of people[8].
        6. **No Discrimination Against Fields of Endeavor**: The license must not restrict anyone from using the software in a specific field or for a particular purpose[8].
        7. **Distribution of License**: The rights attached to the program must apply to all to whom the program is redistributed without the need for execution of an additional license by those parties[8].
        8. **License Must Not Be Specific to a Product**: The license must not be specific to a product and must not restrict the program from being used on any other software[8].
        9. **License Must Not Restrict Other Software**: The license must not place restrictions on other software that is distributed along with the licensed software[8].
        10. **License Must Be Technology-Neutral**: The license must not be specific to any particular technology or interface[8].
    - 原文に "open-source" と書いてあっても、BLOOMやGPT-Jのようなモデル以外は「オープンウェイトモデル」と訳してください。

4. 「了解しました」などの挨拶や余計な返答は含めず、要約記事のみを出力してください。

5. 出力例
<output example>
# 1. Grok-3の性能評価と論争

xAIの新しいLLM、Grok-3の性能に関する議論が活発です。一部のユーザーからは、Grok-3が他の主要なLLM（Gemini 2 ProやChatGPT Proなど）を上回るとの報告もあります。
https://twitter.com/BorisMPower/status/1892407015038996740

👉Grok-3は、xAIが開発した最新のAIモデルで、以下の特徴があります：

## 1. 推論能力と知識
Grok-3は、特に数学や科学の分野で高い推論能力を示しています。例えば、複雑な数学の問題を解く際に、人間のような思考過程を示すことができます。

例: 「2次方程式 x^2 - 5x + 6 = 0 の解を求めよ」という問題に対して、Grok-3は以下のように段階的に解答できます：
  1. 判別式 D = b^2 - 4ac を計算
  2. 解の公式 x = (-b ± √D) / (2a) を適用
  3. 最終的な解 x = 3 または x = 2 を導出

## 2. 実時間情報の取得
実時間情報とは、最新のデータや出来事のことを指します。Grok-3は、リアルタイム検索機能を持っており、最新のニュースや情報を即座に取得し、回答に反映させることができます。

例: 「今日の東京の天気は？」という質問に対して、Grok-3は現在の気象データを参照し、最新の天気情報を提供できます。

ただし、Grok-3は性能面で様々な意見があり、ベンチマーク結果の解釈には注意が必要です。xAIと他社のLLM比較は今後も注目。さらに高性能を追求した計算資源の増強もポイントです。

# 2. DeepSeek R1の躍進:

DeepSeek-R1が、SuperGPQAベンチマークで61.82%という最高精度を達成し、他の主要なLLMを上回りました。
https://x.com/iScienceLuvr/status/1892879645223375319

👉DeepSeek-R1は、特定の分野(科学的推論)において、他のLLMに匹敵、もしくは凌駕する可能性があります。オープンウェイトであるため、今後の発展と応用範囲拡大が期待されます。

## SuperGPQAベンチマークとは
SuperGPQAは、高度な質問応答システムのパフォーマンスを評価するためのベンチマークデータセットです。このデータセットは、AIモデルが複雑な質問にどれだけ正確に答えるかを測定するために使用されます。

## DeepSeek-R1の特徴
DeepSeek-R1は、Mixture-of-Experts (MoE)アーキテクチャを使用し、強化学習によって推論能力が向上した大規模言語モデルです13。このモデルは、オープンウェイトであり、コスト効率が高く、数学やプログラミングタスクで高い精度を示しています。

## 61.82%という精度の意味
61.82%という精度は、SuperGPQAベンチマークでDeepSeek-R1が質問に正しく答える割合を示しています。このスコアが他の主要なLLMを上回ったことは、DeepSeek-R1が質問応答タスクにおいて非常に優れた性能を持っていることを示しています。

## どうしてDeepSeek-R1が優れているのか
DeepSeek-R1が優れている理由は以下の通りです：
  - アーキテクチャと学習手法: MoEアーキテクチャと強化学習を組み合わせたことで、複雑な推論タスクに強みを持っています。
  - オープンウェイト: 自由にカスタマイズできるため、特定のタスクに最適化しやすい利点があります。
  - コスト効率: 高い性能を維持しつつ、コストが低いため、実用的な利用が可能です。

これらの特徴が、DeepSeek-R1がSuperGPQAベンチマークで高い精度を達成する要因となっています。
</output example>

6. 以下がXMLコンテンツです:
{xml_content}
"""

    try:
        response = client.models.generate_content(
            model=model,
            contents=prompt.format(xml_content=xml_content),
        )
        return response.text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None


def main():
    start_time = time.time()
    # Load Gemini API key from environment variables
    GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY or GOOGLE_API_KEY not found in environment variables")
        return
    GEMINI_MODEL = "gemini-2.5-flash-preview-06-17"
    ARCHIVE_URL = "https://buttondown.com/ainews/archive/"

    # Print URL with title
    print("AIニュース要約 \"AI News\" 解説 by " + GEMINI_MODEL)

    # Fetch latest article content
    html_content = fetch_latest_article(ARCHIVE_URL)
    if not html_content:
        end_time = time.time()
        print(f"\n({end_time - start_time:.2f} seconds)")
        return

    # Analyze with Gemini
    result = analyze_with_gemini(html_content, GEMINI_API_KEY, GEMINI_MODEL)

    if result:
        result = re.sub(r"\[(.*?)\]\((.*?)\)", r"\2", result)
        print(result)

    end_time = time.time()
    print(f"\n({end_time - start_time:.2f} seconds)")


if __name__ == "__main__":
    main()
