import requests
import google.generativeai as genai
import re
import time
from bs4 import BeautifulSoup
import warnings
import tweepy
import os
from dotenv import load_dotenv
from twitter_text_utils import TwitterTextValidator, safe_truncate_post, validate_post_text


def fetch_content(url):
    """Fetch The newsletter content"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse XML content using BeautifulSoup
        soup = BeautifulSoup(response.text, "xml")

        # Find the first item tag
        first_item = soup.find("item")

        if first_item:
            # Extract the URL from the link tag
            link_tag = first_item.find("link")
            if link_tag:
                return link_tag.text, str(first_item)
            else:
                print("No link tag found in the first item")
                return None, None
        else:
            print("No item tags found in the XML content")
            return None, None

    except requests.RequestException as e:
        print(f"Error fetching The Batch content: {e}")
        return None, None


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


def analyze_with_gemini(content, api_key, model):
    """Analyze content using Gemini model"""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name=model)

    prompt = """
以下のニュースレターの内容を分析し、**すべての記事について**、以下の構成で日本語で出力してください。**各記事ごとに必ず個別のセクションを作成し、すべての記事を漏れなくまとめてください。**
出力は**Markdown形式**で、各記事ごとに見出し・要約・詳細解説の複数段落で構成してください。

1. 各記事について、以下の順でまとめること：
   - 見出し（日本語訳、Markdownの「#」で大見出し）
   - 150字程度の要約（「## 要約」の小見出し）
   - そのトピックが注目に値する理由と技術について具体例を交えて解説（「## トピック解説」の小見出し、800字程度、複数段落可）
   - 広告記事は無視する

2. 注意事項：
   - 「以下、ニュースレターの内容を分析し…」などのメタな説明は不要。すぐに内容を始める
   - 見出しも日本語に訳す
   - 技術的な概念は平易な言葉で説明
   - 実際の応用例や具体例を含める
   - トピックにおける最重要な人物やチームを自然な文脈で紹介する
   - トピックが重複する場合は次のトピックに進む

3. 出力例（Markdown形式）：
<output example>
# 音声認識の新展開
## 要約
音声認識システムにおける話者の発話検出（VAD）と対話の順番管理について解説。現在のシステムは順番制の対話を基本としているが、より自然な対話を目指して双方向のリアルタイム音声ストリーミングなど新しいアプローチが登場しています。

## トピック解説
Kyutai Labsは2024年7月3日にMoshiを発表しました。Moshiは、リアルタイムでマルチモーダルなデータを処理できる革新的なAIモデルです。Moshiの主要な技術革新の1つは、ユーザーとMoshi間の双方向の持続的な音声ストリームを可能にしたことです。

具体的には：
1. 同時に2つの音声ストリームを処理できる能力を持っており、聞きながら話すことができます。
2. リアルタイムで音声を生成しながら、テキストによる思考の流れを維持することができます。
3. フルデュプレックスの会話が可能で、自然な人間の対話を模倣しています。

これらの機能により、Moshiは従来のチャットボットとは異なり、より自然で直感的なコミュニケーションを実現しています。Moshiの基盤となっているのは、Kyutaiが開発した7ビリオンパラメータの言語モデルHeliumです。このモデルはテキストと音声のコーデックを同時に処理する高性能なシステムを備えています。
なお、Kyutai LabsはMoshiのコードと重みを公開しており、研究者やデベロッパーがこの技術を深く研究し、必要に応じて修正や拡張ができるようにしています。

Moshi Voice AIは、従来のVAD（Voice Activity Detection）技術の限界を超えた革新的なアプローチを採用しています。
Moshiの主な特徴と従来のVADとの違いは以下の通りです：

- マルチモーダル処理: Moshiはテキストと音声を同時に処理できるマルチモーダルモデルです。これにより、単なる音声の検出だけでなく、会話の文脈や感情も理解できます。
- リアルタイム双方向通信: ユーザーとMoshi間で持続的な双方向音声ストリームを実現し、同時に聞きながら話すことができます。
- 感情表現: 70以上の感情を表現し、様々なスタイルで話すことができます。これは従来のVADでは不可能だった機能です。
- 高度な言語モデル: 7ビリオンパラメータの言語モデル「Helium」を基盤としており、高度な自然言語処理能力を持っています。
- インタラプタビリティ: 会話中に中断されても対応できる柔軟性があります。

これらの特徴により、MoshiはVADの単純な音声検出機能を大きく超え、より自然で豊かなコミュニケーションを可能にしています。従来のVADが抱えていた雑音環境下での性能低下や、文脈理解の欠如といった問題を、AIによる高度な処理で解決しているといえます。
</output example>

4. **必ずすべての記事について、上記の形式で個別にまとめてください。1つの記事だけで終わらず、すべての記事を順番に出力してください。** 以下が分析対象の記事です：
{content}
"""

    try:
        response = model.generate_content(contents=prompt.format(content=content))

        # Check if response has valid parts before accessing .text
        if response.candidates and response.candidates[0].content.parts:
            return response.text
        else:
            # Check finish reason to provide specific error message
            if response.candidates:
                reason = response.candidates[0].finish_reason
                if reason == 4:  # RECITATION - copyrighted material detected
                    print("Error calling Gemini API: Response blocked due to copyrighted material detection")
                    print("The newsletter content may contain copyrighted text that the model cannot reproduce.")
                else:
                    print(f"Error calling Gemini API: No content returned (finish_reason: {reason})")
            else:
                print("Error calling Gemini API: No candidates returned")
            return None

    except ValueError as e:
        # Handle response.text accessor failures
        if "response.text" in str(e) and "finish_reason" in str(e):
            print(f"Error calling Gemini API: Response blocked (likely copyrighted material)")
        else:
            print(f"Error calling Gemini API: {e}")
        return None
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None


def main():
    start_time = time.time()
    # Load environment variables
    load_dotenv()

    # Load Gemini API key from environment variables
    GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY or GOOGLE_API_KEY not found in environment variables")
        return
    GEMINI_MODEL = "gemini-3-flash-preview"
    NEWS_URL = "https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml"
    
    missing = _missing_x_creds()
    if missing:
        print(f"[Posting] Warning: Missing X credentials: {', '.join(missing)}")
        print("[Posting] Will skip posting and only print the composed posts.")

    # Fetch content
    url, content = fetch_content(NEWS_URL)
    if not content:
        end_time = time.time()
        print(f"\n({end_time - start_time:.2f} seconds)")
        return

    # Print URL with title
    print('AIニュースレター "The Rundown AI" 解説 by ' + GEMINI_MODEL)
    print("出典： " + url)
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
                            post_text = f"{first_paragraph}\n{url}"

                            # Use proper weighted character validation
                            validation = validate_post_text(post_text, debug=True)
                            if not validation['is_valid']:
                                # Calculate available space for paragraph (280 - URL length - newline)
                                url_weight = TwitterTextValidator.calculate_weighted_length(f"\n{url}")['weighted_length']
                                available_weight = 280 - url_weight

                                if available_weight > 6:  # Reserve space for ellipsis
                                    truncated_paragraph = safe_truncate_post(first_paragraph, available_weight)
                                    post_text = f"{truncated_paragraph}\n{url}"
                                else:
                                    post_text = url
                            
                            posts.append(post_text)
                            break
            
            # Post in reversed order with 1 second pause between posts
            for i, post_text in enumerate(reversed(posts)):
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
