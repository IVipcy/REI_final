# static_qa_data.py - 静的なQ&Aデータと文脈に応じた提案機能

# 静的なQ&Aレスポンス
static_qa_responses = {
    # 基本的な質問
    "京友禅とは": "京都で300年以上続く染色技法で着物に絵を描くように色鮮やかな模様を手作業で染めていきます。成人式や結婚式など、特別な日の着物に使われる「着られる芸術作品」なんです。",
    
    "あなたは誰": "私は京友禅職人のREIです。伝統的な染色技術を受け継ぎ、美しい着物を作っています。",
    
    "どんな作品を作っていますか": "主に振袖、訪問着、帯などを手がけています。四季の花々や古典的な文様を、現代的な感覚で表現することを心がけています。",
    
    # 技術的な質問
    "友禅の工程": "友禅染めには、下絵→糊置き→色挿し→蒸し→水洗い→仕上げという主要な工程があります。各工程で職人の技が光ります。",
    
    "使う道具": "筆、刷毛、糊筒、染料、蒸し器などを使います。特に糊筒の扱いは長年の修行が必要です。",
    
    # 文化的な質問
    "着物の魅力": "着物は日本の美意識が凝縮された衣装です。季節感、色彩の調和、そして着る人の個性を表現できる点が魅力です。",
    
    "伝統を守る": "技術の継承は大切ですが、時代に合わせた新しい表現も必要です。伝統と革新のバランスを大切にしています。"
}

def get_contextual_suggestions(context=None):
    """
    文脈に応じた提案を返す関数
    
    Args:
        context: 現在の会話の文脈（オプション）
    
    Returns:
        list: 提案される質問のリスト
    """
    # デフォルトの提案
    default_suggestions = [
        "京友禅について教えて",
        "どんな作品を作っていますか？",
        "友禅の工程を説明してください",
        "着物の魅力は何ですか？"
    ]
    
    # 文脈がない場合はデフォルトを返す
    if not context:
        return default_suggestions
    
    # 文脈に応じた提案
    context_lower = context.lower()
    
    if "技術" in context or "工程" in context:
        return [
            "使う道具について教えて",
            "一番難しい工程は？",
            "修行期間はどのくらい？",
            "色の調合について"
        ]
    
    elif "伝統" in context or "文化" in context:
        return [
            "伝統を守ることについて",
            "現代との融合は？",
            "後継者育成について",
            "海外での反応は？"
        ]
    
    elif "作品" in context or "着物" in context:
        return [
            "最近の作品について",
            "デザインの着想は？",
            "季節の表現について",
            "お客様との対話"
        ]
    
    # その他の場合はデフォルトを返す
    return default_suggestions

# エクスポート可能な関数として定義
def get_static_response(query):
    """
    静的なレスポンスを取得する関数
    
    Args:
        query: ユーザーの質問
    
    Returns:
        str or None: 該当するレスポンス、または None
    """
    # 完全一致を試す
    if query in static_qa_responses:
        return static_qa_responses[query]
    
    # 部分一致を試す
    query_lower = query.lower()
    for key, response in static_qa_responses.items():
        if key.lower() in query_lower or query_lower in key.lower():
            return response
    
    return None 

# ============================================================================
# 🎯 段階別Q&Aシステム
# ============================================================================

# 段階別Q&Aデータ
staged_qa_responses = {
    # 🎯 段階1：京友禅の概要把握
    'stage1_overview': {
        "京友禅とは何ですか": "京都で300年以上前から続く伝統的な染色方法で、まるで絵を描くように着物に色鮮やかな模様を描いていきます。一つ一つ手作業で作られた着物は、まさに「着られる芸術作品」。成人式の振袖や結婚式の訪問着など、人生の大切な場面で着る美しい着物の多くが、この京友禅の技術で作られているんです。",
        
        "友禅染の歴史を教えて": "17世紀後期に宮崎友禅斎という絵師が始めたんです。それまでの染色とは違って、絵画的な表現ができるようになったのが革命的だったんですよ。",
        
        "他の染色技法との違いは": "友禅の一番の特徴は、糸目糊で輪郭を描くことで、糊が防波堤の役割になって色が混じらないようにすることです。まるで絵を描くように、自由に色を使えるのが他とは違うところですね。",
        
    },
    
    # 🎯 段階2：技術詳細
    'stage2_technical': {
        "のりおき工程って何": "糸目糊で模様の輪郭を描く工程です。ケーキのデコレーションで生クリームを絞るみたいに、下絵のデザインを糊で縁取っていくんです。これが一番難しい工程ですよ。",
                        
        "一番難しい技術は": "やっぱりのりおきですね。手が震えたら線がガタガタになりますし、糊が薄すぎても厚すぎてもダメ。15年やっていても緊張します。",
                
    },
    
    # 🎯 段階3：職人個人・その他
    'stage3_personal': {
        "職人になったきっかけ": "大学で美術を学んでいたんですが、友禅の美しさに魅かれて。最初は会社員だったんですが、やっぱり諦められなくて弟子入りしたんです。",
        
        "15年間で一番大変だったこと": "最初の5年は本当に大変でした。糊筒がうまく扱えなくて、何度もやり直し。師匠には厳しく指導されて、泣きながら練習したこともあります。",
        
        "仕事のやりがいは": "お客さんが着物を着て「きれい」って言ってくれる瞬間ですね。結婚式で花嫁さんが私の作った振袖を着てくれた時は、もう涙が出そうになりました。",
        
        "一日のスケジュール": "朝8時から工房に入って、夕方6時まで作業です。集中力がいる仕事なので、お昼休みはしっかり取るようにしています。",
        
        "将来の夢": "若い人にも友禅の魅力を伝えたいです。体験教室とかもやっていますが、もっと気軽に触れてもらえる場を作りたいんです。",
        
        "プライベートは": "そうですねぇ。実はゲームが大好きで夢中になって気づいたら夜に！なんてこともよくあります。",
        
        "後継者について": "技術を次の世代に残すために教室を開いて職人を目指している方に魅力をつたえています。でも昔みたいな厳しい弟子制度じゃなくて、楽しく学べる環境を作りたいと思っています。",
        
        "海外での反応": "外国の方にも人気ですよ。特にアメリカやヨーロッパの人は、手作業の技術にすごく感動してくれます。日本の文化を誇らしく思う瞬間ですね。",
        
        # 🆕 追加のQ&A
        "師匠との思い出は": "厳しかったけど、本当に尊敬しています。ある日、失敗して落ち込んでいた時に「完璧を目指すな、美しさを目指せ」って言われたんです。その言葉は今でも心に残っていますね。",
        
        "印象に残っている作品は": "3年前に作った桜吹雪の振袖です。数百枚の花びらを一つ一つ描いて、風に舞う感じを表現しました。お客様が「まるで桜の下に立っているみたい」って喜んでくれて、職人冥利に尽きました。",
        
        "お客様とのエピソード": "娘さんの成人式用に振袖を作ったお母さんが、後日写真を持って来てくれたんです。「娘が一生の宝物だって言ってます」って。そういう言葉を聞くと、この仕事を選んで本当に良かったって思います。",
        
        "失敗から学んだこと": "大きな失敗をした時、最初は隠そうとしたんです。でも師匠に「失敗は恥じゃない、隠すのが恥だ」って言われて。それ以来、失敗を素直に認めて、そこから学ぶようにしています。",
        
        "休日の過ごし方": "完全にオフにする日は美術館巡りとか、カフェでのんびり過ごします。でも結局、着物や工芸品を見に行っちゃうんですよね。職業病かもしれません（笑）",
        
        "趣味はある": "ゲームと読書です！特にRPGが好きで、ファンタジーの世界観に浸るのが好きなんです。あとは時代小説も読みます。江戸時代の職人の話とか、すごく勉強になるんですよ。",
        
        "家族は仕事を応援してくれる": "最初は両親が心配してました。「安定した仕事の方が」って。でも今では一番の応援団です。母なんて、友達に自慢してるみたいで恥ずかしいんですけどね（笑）"
    }
}

# 🔧 修正①：段階別サジェスチョンを大幅に増量（5-8個 → 12-15個）
staged_suggestions = {
    # 段階1：概要把握のサジェスチョン（5個 → 12個に増量）
    'stage1_overview': [
        "京友禅とは何ですか？",
        "友禅染の歴史を教えて",
        "他の染色技法との違いは？",
    ],
    
    # 段階2：技術詳細のサジェスチョン（7個 → 15個に増量）
    'stage2_technical': [
        "のりおき工程って何？",
        "一番難しい技術は？",
    ],
    
    # 段階3：職人個人・その他のサジェスチョン（8個 → 15個に増量）
    'stage3_personal': [
        "職人になったきっかけは？",
        "15年間で一番大変だったこと",
        "仕事のやりがいは？",
        "一日のスケジュール",
        "将来の夢は？",
        "プライベートはどう過ごす？",
        "後継者について",
        "海外での反応は？",
        # 🆕 追加のサジェスチョン
        "師匠との思い出は？",
        "印象に残っている作品は？",
        "お客様とのエピソード",
        "失敗から学んだこと",
        "休日の過ごし方",
        "趣味はある？",
        "家族は仕事を応援してくれる？"
    ]
}

# 🔧 修正②：閾値の変更（3→5、7→12）
def get_current_stage(selected_suggestions_count):
    """
    選択されたサジェスチョン数から現在の段階を判定
    
    Args:
        selected_suggestions_count: これまでに選択されたサジェスチョン数
    
    Returns:
        str: 現在の段階 ('stage1_overview', 'stage2_technical', 'stage3_personal')
    """
    if selected_suggestions_count < 3:  # 0, 1, 2 → stage1
        return 'stage1_overview'
    elif selected_suggestions_count < 5:  # 3, 4 → stage2
        return 'stage2_technical'
    else:  # 5以上 → stage3
        return 'stage3_personal'

def get_staged_suggestions(stage, selected_suggestions=[]):
    """
    段階に応じたサジェスチョンを生成（重複排除機能付き）
    
    Args:
        stage: 現在の段階
        selected_suggestions: これまでに選択されたサジェスチョンのリスト
    
    Returns:
        list: 提案される質問のリスト（最大3個）
    """
    import random
    
    # 指定された段階のサジェスチョンを取得
    stage_suggestions = staged_suggestions.get(stage, [])
    
    # 重複を排除
    available_suggestions = [s for s in stage_suggestions if s not in selected_suggestions]
    
    # 3個以下の場合はそのまま返す
    if len(available_suggestions) <= 3:
        return available_suggestions
    
    # 3個をランダムに選択
    return random.sample(available_suggestions, 3)

def get_staged_response(query, stage=None):
    """
    段階別Q&Aから回答を取得
    
    Args:
        query: ユーザーの質問
        stage: 検索対象の段階（Noneの場合は全段階を検索）
    
    Returns:
        str or None: 該当するレスポンス、または None
    """
    # 特定の段階が指定されている場合
    if stage and stage in staged_qa_responses:
        qa_data = staged_qa_responses[stage]
        
        # 完全一致を試す
        if query in qa_data:
            return qa_data[query]
        
        # 部分一致を試す
        query_lower = query.lower()
        for key, response in qa_data.items():
            if key.lower() in query_lower or query_lower in key.lower():
                return response
    
    # 全段階を検索
    for stage_name, qa_data in staged_qa_responses.items():
        # 完全一致を試す
        if query in qa_data:
            return qa_data[query]
        
        # 部分一致を試す
        query_lower = query.lower()
        for key, response in qa_data.items():
            if key.lower() in query_lower or query_lower in key.lower():
                return response
    
    return None 

# ============================================================================
# 🎯 英語版Q&Aシステム
# ============================================================================

# 既存static_qa_responsesの英語版
static_qa_responses_en = {
    # Basic questions
    "What is Kyoto Yuzen": "Kyo-Yuzen is a traditional dyeing technique that's been practiced in Kyoto for over 300 years. It's characterized by gorgeous, delicate patterns that look like paintings on silk. We use a special paste resist technique to create intricate designs on kimono and obi.",
        
    "Tell me about Kyoto Yuzen": "Kyo-Yuzen is a traditional Japanese dyeing art from Kyoto. It features vibrant colors and detailed patterns created using a paste-resist technique. Each piece is hand-painted, making every kimono unique and special.",
    
    "Who are you": "I'm REI, a Kyo-Yuzen craftsman with 15 years of experience. I specialize in hand-painted Yuzen, creating beautiful kimono with traditional techniques passed down through generations.",
    
    "What kind of works do you create": "I mainly create furisode (formal kimono for young women), homongi (visiting kimono), and obi (kimono sashes). I love expressing seasonal flowers and classical patterns with a modern touch - keeping tradition alive while adding contemporary flair.",
    
    "What is the Yuzen process": "The Yuzen process involves sketching → paste application (norioki) → color painting → steaming → washing → finishing. Each step requires specialized skills, and the entire process can take months to complete.",
    
    "What tools do you use": "We use brushes, paste tubes (tsutsu), dyes, steamers, and bamboo frames. The paste tube is particularly important - it takes years to master controlling the fine lines we draw with it.",
    
    "What is the charm of kimono": "Kimono embodies Japanese aesthetics - seasonal expression, color harmony, and individual personality. It's wearable art that connects past and present, tradition and personal style."
}

# 英語版段階別Q&Aデータ
staged_qa_responses_en = {
    # 🎯 Stage 1: Overview
    'stage1_overview': {
        "What is Kyo-Yuzen": "Kyo-Yuzen is a 300-year-old traditional dyeing method from Kyoto where we literally paint on kimono fabric like creating a piece of art. Each kimono is handmade, making it truly wearable art. Most of the beautiful formal kimono worn at weddings and coming-of-age ceremonies are created using this technique.",
        
        "Tell me about the history of Yuzen dyeing": "It was started by a painter named Miyazaki Yuzen-sai in the late 17th century. He revolutionized textile dyeing by applying painting techniques to fabric, creating designs as beautiful as paintings. Before this, dyeing methods were much more limited in their artistic expression.",
        
        "What's the difference from other dyeing techniques": "The main difference is our use of paste resist (norioki) to create fine outlines that prevent colors from bleeding together. This allows us to paint freely within the lines, just like creating a watercolor painting. Other techniques like shibori use binding or folding, but Yuzen gives us complete artistic freedom.",
        
    },
    
    # 🎯 Stage 2: Technical Details
    'stage2_technical': {
        "What is the norioki process": "Norioki is the paste application process - the heart of Yuzen dyeing. We use a cone-shaped tube, like a pastry bag, to draw fine lines with rice paste. This creates barriers that prevent dyes from bleeding, allowing us to paint intricate designs. It requires incredible hand control and years of practice.",
        
        "What's the most difficult technique": "Definitely the paste application (norioki). Your hand must be perfectly steady to create smooth, consistent lines. If the paste is too thin, it won't resist the dye. Too thick, and it cracks. Even after 15 years, I still hold my breath during delicate sections!",
        
    },
    
    # 🎯 Stage 3: Personal & Miscellaneous
    'stage3_personal': {
        "What led you to become a craftsman": "I studied art in university and fell in love with Yuzen's beauty. I tried working a regular office job first, but couldn't stop thinking about it. Eventually, I quit and apprenticed myself to a master craftsman. Best decision I ever made!",
        
        "What was the hardest thing in 15 years": "The first five years were brutal. I couldn't control the paste tube properly and had to redo work constantly. My master was strict - I cried during practice more times than I can count. But those tears turned into skills.",
        
        "What's rewarding about your work": "When customers see their finished kimono and say 'it's beautiful' - that moment makes everything worthwhile. Once, a bride wore my furisode at her wedding and I almost cried seeing how happy she looked. That's why I do this.",
        
        "Your daily schedule": "I'm in the workshop from 8 AM to 6 PM. This work requires intense concentration, so I make sure to take a proper lunch break. Can't create beauty when you're exhausted!",
        
        "Your future dreams": "I want to share Yuzen's beauty with younger generations. I already run workshops, but I'd love to create more opportunities for people to experience this art firsthand. Make it accessible and exciting, not intimidating.",
        
        "How do you spend your private time": "Honestly? I'm a huge gamer! Sometimes I get so absorbed in games that I look up and it's suddenly midnight. It's my way of unwinding after a day of intense focus. Balance is important!",
        
        "About successors": "Passing on these techniques is our responsibility, but the old strict apprentice system doesn't work anymore. Young people need encouragement, not just criticism. I try to create a fun learning environment while still maintaining high standards. The craft must survive, but it also must evolve.",
        
        "Reactions from overseas": "International visitors are always amazed by the detail and handwork. Americans and Europeans especially appreciate that every piece is unique, not mass-produced. They often say it's like wearing art. It makes me proud to share Japanese culture through my work.",
        
        # 🆕 Additional Q&A
        "Memories with your master": "He was strict but I really respect him. One day when I was feeling down after a failure, he told me 'Don't aim for perfection, aim for beauty.' Those words still stay with me today.",
        
        "Your most memorable work": "A cherry blossom furisode I created three years ago. I painted hundreds of individual petals to express the feeling of wind blowing through cherry blossoms. When the customer said 'it's like standing under real cherry trees,' I felt such fulfillment as a craftsman.",
        
        "Episodes with customers": "A mother who commissioned a furisode for her daughter's coming-of-age ceremony brought photos to me later. She said 'My daughter says it's a treasure for life.' Hearing words like that makes me feel I really chose the right career.",
        
        "Lessons from failures": "When I made a big mistake, I initially tried to hide it. But my master said 'Failure isn't shameful, hiding it is.' Since then, I've learned to acknowledge my mistakes honestly and learn from them.",
        
        "How do you spend weekends": "On my complete days off, I visit art museums or relax at cafes. But I end up looking at kimono and crafts anyway. It's probably an occupational hazard! (laughs)",
        
        "Any hobbies": "Gaming and reading! I especially love RPGs - I love immersing myself in fantasy worlds. I also read historical novels. Stories about Edo-period craftsmen are really educational.",
        
        "Does your family support your work": "At first, my parents worried. They said 'Wouldn't a stable job be better?' But now they're my biggest supporters. My mom even brags to her friends, which is a bit embarrassing! (laughs)"
    }
}

# 🔧 修正③：英語版段階別サジェスチョンも増量（5-8個 → 12-15個）
staged_suggestions_en = {
    # Stage 1: Overview suggestions（5個 → 12個に増量）
    'stage1_overview': [
        "What is Kyo-Yuzen?",
        "Tell me about the history of Yuzen dyeing",
    ],
    
    # Stage 2: Technical detail suggestions（7個 → 15個に増量）
    'stage2_technical': [
        "What is the norioki process?",
        "What's the most difficult technique?",
    ],
    
    # Stage 3: Personal craftsman & other suggestions（8個 → 15個に増量）
    'stage3_personal': [
        "What led you to become a craftsman?",
        "What was the hardest thing in 15 years?",
        "What's rewarding about your work?",
        "Your daily schedule",
        "Your future dreams?",
        "How do you spend your private time?",
        "About successors",
        "Reactions from overseas?",
        # 🆕 追加のサジェスチョン
        "Memories with your master?",
        "Your most memorable work?",
        "Episodes with customers",
        "Lessons from failures",
        "How do you spend weekends?",
        "Any hobbies?",
        "Does your family support your work?"
    ]
}

# ============================================================================
# 🎯 多言語対応関数
# ============================================================================

def get_static_response_multilang(query, language='ja'):
    """
    多言語対応の静的レスポンス取得関数
    
    Args:
        query: ユーザーの質問
        language: 言語コード ('ja' または 'en')
    
    Returns:
        str or None: 該当するレスポンス、または None
    """
    # クエリの前処理（空白削除、小文字化、句読点削除）
    query = query.strip()
    query_lower = query.lower()
    # 末尾の句読点を削除
    query_normalized = query_lower.rstrip('?!.。？！')
    
    # デバッグログ
    print(f"[DEBUG] Static Q&A search - Query: '{query}', Normalized: '{query_normalized}', Language: {language}")
    
    if language == 'en':
        # 英語版から検索
        # 完全一致を試す（大文字小文字と句読点を無視）
        for key, response in static_qa_responses_en.items():
            key_normalized = key.lower().rstrip('?!.')
            if key_normalized == query_normalized:
                print(f"[DEBUG] Static Q&A hit (exact match): '{key}'")
                return response
        
        # 部分一致を試す（より柔軟なマッチング）
        for key, response in static_qa_responses_en.items():
            key_lower = key.lower()
            key_normalized = key_lower.rstrip('?!.')
            # キーが質問に含まれるか、質問がキーに含まれるか
            if key_normalized in query_normalized or query_normalized in key_normalized:
                print(f"[DEBUG] Static Q&A hit (partial match): '{key}'")
                return response
            
            # 単語レベルでのマッチング
            key_words = set(key_normalized.split())
            query_words = set(query_normalized.split())
            # 重要な単語が共通しているか
            common_words = key_words & query_words
            if len(common_words) >= 2 and any(word in common_words for word in ['kyoto', 'yuzen', 'kyo-yuzen', 'history', 'characteristics', 'process']):
                print(f"[DEBUG] Static Q&A hit (word match): '{key}'")
                return response
    else:
        # 日本語版から検索（既存関数を活用）
        return get_static_response(query)
    
    print(f"[DEBUG] Static Q&A miss - No match found")
    return None

def get_staged_response_multilang(query, language='ja', stage=None):
    """
    多言語対応の段階別Q&A取得関数
    
    Args:
        query: ユーザーの質問
        language: 言語コード ('ja' または 'en')
        stage: 検索対象の段階（Noneの場合は全段階を検索）
    
    Returns:
        str or None: 該当するレスポンス、または None
    """
    # クエリの前処理（空白削除、小文字化、句読点削除）
    query = query.strip()
    query_lower = query.lower()
    query_normalized = query_lower.rstrip('?!.。？！')
    
    # デバッグログ
    print(f"[DEBUG] Staged Q&A search - Query: '{query}', Normalized: '{query_normalized}', Language: {language}, Stage: {stage}")
    
    # 言語に応じてデータソースを選択
    if language == 'en':
        qa_data_source = staged_qa_responses_en
    else:
        qa_data_source = staged_qa_responses
    
    # 特定の段階が指定されている場合
    if stage and stage in qa_data_source:
        qa_data = qa_data_source[stage]
        
        # 完全一致を試す（大文字小文字と句読点を無視）
        for key, response in qa_data.items():
            key_normalized = key.lower().rstrip('?!.')
            if key_normalized == query_normalized:
                print(f"[DEBUG] Staged Q&A hit (exact match): '{key}' in stage {stage}")
                return response
        
        # 部分一致を試す
        for key, response in qa_data.items():
            key_lower = key.lower()
            key_normalized = key_lower.rstrip('?!.')
            if key_normalized in query_normalized or query_normalized in key_normalized:
                print(f"[DEBUG] Staged Q&A hit (partial match): '{key}' in stage {stage}")
                return response
    
    # 全段階を検索
    for stage_name, qa_data in qa_data_source.items():
        # 完全一致を試す
        for key, response in qa_data.items():
            key_normalized = key.lower().rstrip('?!.')
            if key_normalized == query_normalized:
                print(f"[DEBUG] Staged Q&A hit (exact match): '{key}' in stage {stage_name}")
                return response
        
        # 部分一致を試す
        for key, response in qa_data.items():
            key_lower = key.lower()
            key_normalized = key_lower.rstrip('?!.')
            if key_normalized in query_normalized or query_normalized in key_normalized:
                print(f"[DEBUG] Staged Q&A hit (partial match): '{key}' in stage {stage_name}")
                return response
    
    print(f"[DEBUG] Staged Q&A miss - No match found")
    return None

def get_staged_suggestions_multilang(stage, language='ja', selected_suggestions=[]):
    """
    多言語対応の段階別サジェスチョン生成関数（重複排除強化版）
    
    Args:
        stage: 現在の段階（数値または文字列）
        language: 言語コード ('ja' または 'en')
        selected_suggestions: これまでに選択されたサジェスチョンのリスト
    
    Returns:
        list: 提案される質問のリスト（最大3個）
    """
    import random
    
    # 数値段階を文字列キーに変換
    if isinstance(stage, int):
        stage_map = {
            1: 'stage1_overview',
            2: 'stage2_technical', 
            3: 'stage3_personal'
        }
        stage_key = stage_map.get(stage, 'stage1_overview')
    elif isinstance(stage, str):
        stage_key = stage
    else:
        stage_key = 'stage1_overview'  # デフォルト
    
    print(f"[DEBUG] Suggestion search - Stage: {stage} -> {stage_key}, Language: {language}")
    print(f"[DEBUG] Selected suggestions (input): {selected_suggestions}")
    
    # 言語に応じてサジェスチョンソースを選択
    if language == 'en':
        suggestions_source = staged_suggestions_en
    else:
        suggestions_source = staged_suggestions
    
    # 指定された段階のサジェスチョンを取得
    stage_suggestions = suggestions_source.get(stage_key, [])
    print(f"[DEBUG] Available suggestions for {stage_key}: {len(stage_suggestions)} items")
    print(f"[DEBUG] Stage suggestions: {stage_suggestions}")
    
    # 重複を排除（大文字小文字を区別しない比較）
    selected_suggestions_lower = {s.lower().strip() for s in selected_suggestions if isinstance(s, str)}
    print(f"[DEBUG] Selected suggestions (normalized): {selected_suggestions_lower}")
    
    # 利用可能なサジェスチョンをフィルタリング
    available_suggestions = []
    for s in stage_suggestions:
        s_normalized = s.lower().strip()
        if s_normalized not in selected_suggestions_lower:
            available_suggestions.append(s)
        else:
            print(f"[DEBUG] Filtering out duplicate: {s}")
    
    print(f"[DEBUG] After duplicate removal: {len(available_suggestions)} items")
    print(f"[DEBUG] Available after filtering: {available_suggestions}")
    
    # 3個以下の場合はそのまま返す
    if len(available_suggestions) <= 3:
        print(f"[DEBUG] Returning all available: {available_suggestions}")
        return available_suggestions
    
    # 3個をランダムに選択（シャッフルして先頭3つを取得）
    shuffled = available_suggestions.copy()
    random.shuffle(shuffled)  # 完全にシャッフル
    selected = shuffled[:3]  # 先頭3つを選択
    
    print(f"[DEBUG] Final selected suggestions: {selected}")
    return selected

def get_contextual_suggestions_multilang(context=None, language='ja'):
    """
    多言語対応の文脈に応じた提案関数
    
    Args:
        context: 現在の会話の文脈（オプション）
        language: 言語コード ('ja' または 'en')
    
    Returns:
        list: 提案される質問のリスト
    """
    if language == 'en':
        # 英語版のデフォルト提案
        default_suggestions = [
            "Tell me about Kyo-Yuzen",
            "What kind of works do you create?",
            "Explain the Yuzen process",
            "What is the charm of kimono?"
        ]
        
        if not context:
            return default_suggestions
        
        # 英語での文脈対応（簡易版）
        context_lower = context.lower()
        
        if "technique" in context or "process" in context:
            return [
                "Tell me about the tools used",
                "What's the most difficult process?",
                "How long is the training period?",
                "About color mixing"
            ]
        elif "tradition" in context or "culture" in context:
            return [
                "About preserving tradition",
                "Fusion with modern times?",
                "About successor training",
                "Reactions from overseas?"
            ]
        elif "work" in context or "kimono" in context:
            return [
                "About recent works",
                "Design inspiration?",
                "About seasonal expression",
                "Dialogue with customers"
            ]
        
        return default_suggestions
    else:
        # 日本語版（既存関数を活用）
        return get_contextual_suggestions(context)

# application.py との互換性のために追加
STATIC_QA_PAIRS = static_qa_responses  # 既存の辞書を参照

# ====================================================================
# 静的Q&Aメディアデータ（画像・動画紐付け）
# ====================================================================
# 注意: メディアはキャッシュしない（URLのみ返却）
# ブラウザの標準キャッシュ機能を活用

qa_media_data = {
    # ====== 日本語質問キー ======
    
    
    "友禅染の歴史を教えて": {
        "images": [
            {
                "url": "/static/media/kyoyuzen/MiyazakiYuzensai.jpg",
                "alt": "京友禅の制作工程",
                "caption": "宮崎友禅斉"
            },
            {
                "url": "/static/media/kyoyuzen/他の染色技法との違いは.jpg",
                "alt": "友禅染の技法",
                "caption": "色鮮やかで写実的な表現"
            }
        ]
    },
    
       "他の染色技法との違いは？": {  
        "videos": [
            {
                "url": "/static/media/kyoyuzen/craftsmanship.mp4",
                "thumbnail": "/static/media/thumbnails/craftsmanship_thumb.jpg",
                "caption": "職人による京友禅の実演"
            }
        ]
    },
    
    # ====== 英語質問キー（将来対応） ======


    "Tell me about the history of Yuzen dyeing": {
        "images": [
            {
                "url": "/static/media/kyoyuzen/MiyazakiYuzensai.jpg",
                "alt": "京友禅の制作工程",
                "caption": "宮崎友禅斉"
            },
            {
                "url": "/static/media/kyoyuzen/他の染色技法との違いは.jpg",
                "alt": "友禅染の技法",
                "caption": "色鮮やかで写実的な表現"
            }
        ]
    }
}


def get_qa_media(question):
    """
    質問に紐付くメディアデータを取得
    
    この関数は質問文からメディアデータを検索します。
    メディアファイル自体はキャッシュせず、URLのみを返します。
    
    Args:
        question (str): 質問テキスト
        
    Returns:
        dict or None: メディアデータ、存在しない場合はNone
        
    Examples:
        >>> get_qa_media("京友禅とは何ですか")
        {'images': [...], 'videos': [...]}
        
        >>> get_qa_media("関係ない質問")
        None
    """
    if not question:
        return None
    
    # 完全一致チェック
    if question in qa_media_data:
        return qa_media_data[question]
    
    # 正規化して完全一致チェック（句読点のみ無視）
    question_normalized = question.replace('?', '').replace('？', '').strip()
    
    for key in qa_media_data.keys():
        key_normalized = key.replace('?', '').replace('？', '').strip()
        
        # 正規化後の完全一致のみ
        if question_normalized == key_normalized:
            return qa_media_data[key]
    
    return None