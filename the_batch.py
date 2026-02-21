import requests
import google.generativeai as genai
import re
import time
from bs4 import BeautifulSoup
import tweepy
import os
from dotenv import load_dotenv
from twitter_text_utils import TwitterTextValidator, safe_truncate_post, validate_post_text


def fetch_latest_article_url(url):
    """Fetch the latest article URL from The Batch newsletter page"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse HTML content
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the first article
        first_article = soup.find("article")
        if not first_article:
            return None

        # Get the article URL from the first <a> tag that is a direct child of the article
        article_link = first_article.find("a", recursive=False)
        article_url = article_link["href"] if article_link and article_link.get("href") else None

        return article_url

    except requests.RequestException as e:
        print(f"Error fetching The Batch article URL: {e}")
        return None


def fetch_article_content(url):
    """Fetch article content from a given URL"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse HTML content
        soup = BeautifulSoup(response.text, "html.parser")

        # ** Assuming the article content is within a div with a specific class or structure **
        # ** This part might need adjustment based on the actual new HTML structure **
        content_element = soup.find("div", class_="c-content-l")  # Example selector, needs verification
        if not content_element:
            content_element = soup.find("article")  # Another common tag

        if content_element:
            content = content_element.get_text(separator="\n", strip=True)
            return content
        else:
            print(f"Error: Could not find the article content in {url}. Content set to 'N/A'.")
            return None

    except requests.RequestException as e:
        print(f"Error fetching article content from {url}: {e}")
        return None


def analyze_with_gemini(content, api_key, model):
    """Analyze content using Gemini model"""
    genai.configure(api_key=api_key)

    prompt = """
以下のHTML形式のコンテンツを分析し、以下の手順に従って記事の要約を作成してください。

1. コンテンツから、広告を除外してください。

2. 冒頭の、Andrew Ngから読者へのメッセージは重要なので、丁寧に解説してください。彼の名前の読みは「アンドリュー・ィン」としてください。

3. 次に、残りの各トピックを以下の形式で記述してください。
    - トピックの見出し
    - 約100字程度の要約
    - 選定したトピックのソースURL（必ず1件）
    - ニュースの注目点を約400字程度にまとめた解説

4. 上記の内容を、日本の読者が読みやすい自然な日本語に翻訳してください。
    - open-weightのモデルのことは「オープンウェイトモデル」と訳してください。
    - 「オープンソース」という用語はできるだけ避け、「オープンウェイト」「寛容なライセンスの」等のように訳してください。
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

5. 「了解しました」などの挨拶や余計な返答は含めず、要約記事のみを出力してください。

6. 出力例
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

7. 以下がHTMLコンテンツです:
{content}
"""

    try:
        model_instance = genai.GenerativeModel(model_name=model)
        response = model_instance.generate_content(contents=prompt.format(content=content))
        return response.text
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None


def _missing_x_creds():
    missing = []
    if not os.getenv("X_CONSUMER_KEY"):
        missing.append("X_CONSUMER_KEY")
    if not os.getenv("X_CONSUMER_SECRET"):
        missing.append("X_CONSUMER_SECRET")
    if not os.getenv("X_ACCESS_TOKEN"):
        missing.append("X_ACCESS_TOKEN")
    if not os.getenv("X_ACCESS_TOKEN_SECRET"):
        missing.append("X_ACCESS_TOKEN_SECRET")
    return missing


def post_to_x(text):
    client = tweepy.Client(
        consumer_key=os.getenv("X_CONSUMER_KEY"),
        consumer_secret=os.getenv("X_CONSUMER_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET"),
    )
    client.create_tweet(text=text)


def main():
    start_time = time.time()
    # Load environment variables
    load_dotenv()
    
    # Get Gemini API key from environment variables
    GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("Error: GOOGLE_API_KEY or GEMINI_API_KEY not found in environment variables")
        return
    GEMINI_MODEL = "gemini-3-flash-preview"
    BATCH_URL = "https://www.deeplearning.ai/the-batch"
    BASE_URL = "https://www.deeplearning.ai"
    
    missing = _missing_x_creds()
    if missing:
        print(f"[Posting] Warning: Missing X credentials: {', '.join(missing)}")
        print("[Posting] Will skip posting and only print the composed posts.")

    # Fetch the latest article URL
    article_url = fetch_latest_article_url(BATCH_URL)
    if not article_url:
        end_time = time.time()
        print(f"\n({end_time - start_time:.2f} seconds)")
        return

    # Construct the full article URL
    full_article_url = BASE_URL + article_url

    # Fetch the content from the full article URL
    content = fetch_article_content(full_article_url)
    if not content:
        end_time = time.time()
        print(f"\n({end_time - start_time:.2f} seconds)")
        return

    # Print URL with title
    print('AIニュースレター "The Batch" 解説 by ' + GEMINI_MODEL)
    print("出典： " + full_article_url)
    print()

    # Analyze with Gemini
    result = analyze_with_gemini(content, GEMINI_API_KEY, GEMINI_MODEL)

    if result:
        result = re.sub(r"\[(.*?)\]\((.*?)\)", r"\2", result)
        print(result)
        
        # Post to X if credentials are available
        if not missing:
            # Extract first paragraphs after headlines
            lines = result.split('\n')
            posts = []
            
            for i, line in enumerate(lines):
                if line.startswith('# '):  # Found a headline
                    # Look for the first non-empty paragraph after the headline
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip() and not lines[j].startswith('#') and not lines[j].startswith('http'):
                            first_paragraph = lines[j].strip()
                            post_text = f"{first_paragraph}\n{full_article_url}"

                            # Use proper weighted character validation
                            validation = validate_post_text(post_text, debug=True)
                            if not validation['is_valid']:
                                # Calculate available space for paragraph (280 - URL length - newline)
                                url_weight = TwitterTextValidator.calculate_weighted_length(f"\n{full_article_url}")['weighted_length']
                                available_weight = 280 - url_weight

                                if available_weight > 6:  # Reserve space for ellipsis
                                    truncated_paragraph = safe_truncate_post(first_paragraph, available_weight)
                                    post_text = f"{truncated_paragraph}\n{full_article_url}"
                                else:
                                    post_text = full_article_url
                            
                            posts.append(post_text)
                            break
            
            # Post in reversed order with 1 second pause between posts
            for i, post_text in enumerate(reversed(posts)):
                # Final validation check before posting
                final_validation = validate_post_text(post_text, debug=True)
                if not final_validation['is_valid']:
                    print(f"WARNING: Post {i+1} still exceeds limit after processing!")
                    post_text = safe_truncate_post(post_text)
                    print(f"Re-truncated to: {post_text}")

                print(f"\nPosting to X ({i+1}/{len(posts)}): {post_text}")
                try:
                    post_to_x(post_text)
                    print("Successfully posted to X!")
                except Exception as e:
                    print(f"[Posting] Error posting to X: {e}")
                
                if i < len(posts) - 1:  # Don't sleep after the last post
                    time.sleep(1)

    end_time = time.time()
    print(f"\n({end_time - start_time:.2f} seconds)")


if __name__ == "__main__":
    main()
