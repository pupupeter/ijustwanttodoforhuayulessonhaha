from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pandas as pd
import random
import os
from services.question_service import QuestionService
from services.content_service import ContentService
from services.tts_service import TTSService

app = Flask(__name__, template_folder='template', static_folder='static')
app.secret_key = "super_secret_key_for_mandarin_quiz"

# Configuration
WORD_FILE = "14452詞語表202504.xlsx"
GRAMMAR_FILE = "臺灣華語文能力基準語法點表_112-01-04(1).xlsx"
MANUAL_QUESTIONS_FILE = "data/manual_questions.json"

# Legacy globals
df_word = None
df_grammar = None
question_service = None
content_service = None
tts_service = None

def load_data():
    global df_word, df_grammar, question_service, content_service, tts_service
    try:
        df_word = pd.read_excel(WORD_FILE)
        df_grammar = pd.read_excel(GRAMMAR_FILE)
        print("✅ 資料載入成功")
    except Exception as e:
        print(f"❌ 載入失敗：{e}")
    try:
        question_service = QuestionService(WORD_FILE, GRAMMAR_FILE, MANUAL_QUESTIONS_FILE)
        print("✅ QuestionService 初始化成功")
    except Exception as e:
        print(f"❌ QuestionService 初始化失敗：{e}")
    try:
        content_service = ContentService("data/practice_content.json")
        print("✅ ContentService 初始化成功")
    except Exception as e:
        print(f"❌ ContentService 初始化失敗：{e}")
    try:
        tts_service = TTSService()
        print("✅ TTSService 初始化成功")
    except Exception as e:
        print(f"❌ TTSService 初始化失敗：{e}")

# Jinja2 filter
@app.template_filter('int_to_char')
def int_to_char(i):
    return chr(65 + i)

# ==================== Quiz Functions ====================

def generate_questions(mode, count=5):
    questions = []
    for _ in range(count):
        quiz = None
        if mode == "1":
            quiz = generate_word_quiz()
        elif mode == "2":
            quiz = generate_grammar_quiz()
        else:
            if random.choice([True, False]):
                quiz = generate_word_quiz()
            else:
                quiz = generate_grammar_quiz()
        if quiz:
            questions.append(quiz)
    return questions

def generate_word_quiz():
    if df_word is None: return None
    target = df_word.sample(n=1).iloc[0]
    word = target['word']
    correct = target['pinyin']
    distractors = df_word[df_word['word'] != word].sample(n=3)['pinyin'].tolist()
    options = distractors + [correct]
    random.shuffle(options)
    return {"type": "單字", "q": f"請問詞語「{word}」的拼音是什麼？", "o": options, "a": correct}

def generate_grammar_quiz():
    if df_grammar is None: return None
    filtered = df_grammar[df_grammar['例句'].notna()]
    target = filtered.sample(n=1).iloc[0]
    gp = target['語法點']
    sent = target['例句']
    q_text = sent.replace(gp, "___", 1) if gp in sent else f"請將「{gp}」填入正確位置：\n{sent}"
    distractors = df_grammar[df_grammar['語法點'] != gp].sample(n=3)['語法點'].tolist()
    options = distractors + [gp]
    random.shuffle(options)
    return {"type": "語法", "q": q_text, "o": options, "a": gp}

def generate_questions_by_topic(topic_name, p_type, count=5):
    questions = []
    for _ in range(count):
        quiz = None
        if p_type == 'voc':
            quiz = generate_word_quiz()
            if quiz: quiz['type'] = f"{topic_name.capitalize()} - 詞彙"
        elif p_type == 'lis':
            quiz = generate_word_quiz()
            if quiz:
                quiz['type'] = f"{topic_name.capitalize()} - 聽力"
                quiz['q'] = "請聽音檔並選擇正確的答案 (模擬)"
        elif p_type == 'dia':
            quiz = generate_grammar_quiz()
            if quiz: quiz['type'] = f"{topic_name.capitalize()} - 對話"
        if quiz:
            questions.append(quiz)
    return questions

# ==================== Page Routes ====================

@app.route('/')
def index():
    return render_template('介面.html', user_name="英雄玩家", progress=65, streak=7)

@app.route('/lobby')
def lobby():
    return render_template('遊戲大廳.html')

@app.route('/settings')
def settings():
    return render_template('設定.html')

@app.route('/friends')
def friends():
    online_friends = [
        {'name': '小明', 'initial': '明', 'gradient': 'from-blue-400 to-blue-600'},
        {'name': 'MeiMei', 'initial': 'M', 'gradient': 'from-pink-400 to-rose-500'},
        {'name': '語言王', 'initial': '王', 'gradient': 'from-purple-400 to-purple-600'},
    ]
    friends_list = [
        {'name': '小明 Xiaoming', 'initial': '明', 'gradient': 'from-blue-400 to-blue-600', 'level': 18, 'score': 12400, 'online': True},
        {'name': 'MeiMei 妹妹', 'initial': 'M', 'gradient': 'from-pink-400 to-rose-500', 'level': 15, 'score': 9800, 'online': True},
        {'name': '語言達人 Pro', 'initial': '達', 'gradient': 'from-purple-400 to-purple-600', 'level': 22, 'score': 8500, 'online': False},
        {'name': 'TaipeiPro 88', 'initial': 'T', 'gradient': 'from-emerald-400 to-teal-500', 'level': 12, 'score': 6200, 'online': False},
        {'name': '台灣通 Master', 'initial': '台', 'gradient': 'from-amber-400 to-orange-500', 'level': 9, 'score': 4100, 'online': False},
    ]
    suggestions = [
        {'name': 'DragonLearner', 'initial': 'D', 'gradient': 'from-red-400 to-red-600', 'level': 11},
        {'name': '普通話王', 'initial': '普', 'gradient': 'from-indigo-400 to-indigo-600', 'level': 7},
    ]
    return render_template('friends.html',
                           online_friends=online_friends,
                           friends=friends_list,
                           suggestions=suggestions)

@app.route('/profile')
def profile():
    achievements = [
        {'name': '首勝', 'icon': 'emoji_events', 'gradient': 'from-yellow-400 to-amber-500'},
        {'name': '連勝 3', 'icon': 'local_fire_department', 'gradient': 'from-orange-400 to-red-500'},
        {'name': '詞彙王', 'icon': 'menu_book', 'gradient': 'from-blue-400 to-blue-600'},
        {'name': '7天連續', 'icon': 'calendar_month', 'gradient': 'from-emerald-400 to-teal-500'},
        {'name': '速答王', 'icon': 'bolt', 'gradient': 'from-purple-400 to-purple-600'},
    ]
    recent_games = [
        {'mode': 'A1A2', 'category': 'Mixed', 'date': '今天', 'correct': 4, 'total': 5, 'result': 'win', 'points': 850},
        {'mode': 'B1B2', 'category': 'Grammar', 'date': '昨天', 'correct': 2, 'total': 5, 'result': 'loss', 'points': 200},
        {'mode': 'A1A2', 'category': 'Vocab', 'date': '2天前', 'correct': 5, 'total': 5, 'result': 'win', 'points': 1200},
        {'mode': 'A1A2', 'category': 'Mixed', 'date': '3天前', 'correct': 3, 'total': 5, 'result': 'win', 'points': 600},
    ]
    return render_template('profile.html',
                           user_name="英雄玩家",
                           progress=65,
                           streak=7,
                           level=15,
                           joined="2025 Jan",
                           total_score=24350,
                           games_played=48,
                           win_rate=73,
                           achievements=achievements,
                           recent_games=recent_games)

@app.route('/topic/<name>')
def topic(name):
    session['last_topic'] = name
    template_map = {
        'cuisine': 'cuisine.html',
        'shopping': 'shopping.html',
        'tourism': 'tourism.html',
        'worklife': 'worklife.html'
    }
    return render_template(template_map.get(name, '介面.html'))

@app.route('/practice/<topic_name>/<p_type>')
def start_practice(topic_name, p_type):
    session['topic'] = topic_name
    session['p_type'] = p_type
    session['score'] = 0
    session['correct_count'] = 0
    session['bot_score'] = 0

    if p_type == 'voc':
        items = content_service.get_items(topic_name, 'vocabulary') if content_service else []
        session['voc_items'] = items
        session['voc_idx'] = 0
        return redirect(url_for('quiz'))

    elif p_type == 'dia':
        items = content_service.get_items(topic_name, 'dialogue') if content_service else []
        questions = []
        for item in items:
            opts = list(item.get('options', []))
            correct_text = next((o['text'] for o in opts if o.get('is_correct')), '')
            opt_texts = [o['text'] for o in opts]
            random.shuffle(opt_texts)
            questions.append({'type': '情境對話', 'q': item.get('question', ''), 'o': opt_texts, 'a': correct_text})
        if not questions:
            questions = generate_questions_by_topic(topic_name, p_type)
        session['questions'] = questions
        session['current_idx'] = 0
        return redirect(url_for('quiz'))

    elif p_type == 'lis':
        items = content_service.get_items(topic_name, 'listening') if content_service else []
        questions = []
        for item in items:
            opts = list(item.get('options', []))
            correct_text = next((o['text'] for o in opts if o.get('is_correct')), '')
            opt_texts = [o['text'] for o in opts]
            random.shuffle(opt_texts)
            questions.append({
                'type': '聽力測驗',
                'q': item.get('audio_text', ''),
                'o': opt_texts,
                'a': correct_text,
                'lis_question': item.get('question', '')
            })
        if not questions:
            questions = generate_questions_by_topic(topic_name, p_type)
        session['questions'] = questions
        session['current_idx'] = 0
        return redirect(url_for('quiz'))

    else:
        session['questions'] = generate_questions_by_topic(topic_name, p_type)
        session['current_idx'] = 0
        return redirect(url_for('quiz'))


@app.route('/voc_next', methods=['POST'])
def voc_next():
    action = request.form.get('action', 'practice')
    idx = session.get('voc_idx', 0)
    if action == 'mastered':
        points = 500
        session['score'] = session.get('score', 0) + points
        session['correct_count'] = session.get('correct_count', 0) + 1
        session['voc_idx'] = idx + 1
        return redirect(url_for('quiz', lp=points, lc=1))
    else:
        session['voc_idx'] = idx + 1
        return redirect(url_for('quiz', lp=0, lc=0))

@app.route('/start_game/<mode>')
def start_game(mode):
    session['questions'] = generate_questions(mode)
    session['current_idx'] = 0
    session['score'] = 0
    session['correct_count'] = 0
    session['bot_score'] = 0
    return redirect(url_for('quiz'))

@app.route('/quiz')
def quiz():
    p_type = session.get('p_type')
    topic = session.get('topic', 'cuisine')
    last_points = request.args.get('lp', -1, type=int)
    last_correct = request.args.get('lc', -1, type=int)

    # Vocabulary flashcard mode
    if p_type == 'voc':
        items = session.get('voc_items', [])
        idx = session.get('voc_idx', 0)
        if not items or idx >= len(items):
            return redirect(url_for('result'))
        return render_template('voc.html',
                               item=items[idx],
                               current_idx=idx,
                               total=len(items),
                               topic=topic,
                               player_score=session.get('score', 0),
                               last_points=last_points,
                               last_correct=last_correct)

    idx = session.get('current_idx', 0)
    questions = session.get('questions', [])

    if idx >= len(questions):
        return redirect(url_for('result'))

    q = questions[idx]

    template_name = '遊戲頁.html'
    if p_type == 'lis':
        template_name = 'lis.html'
    elif p_type == 'dia':
        template_name = 'dia.html'

    try:
        t_path = os.path.join(app.template_folder, template_name)
        if not os.path.exists(t_path) or os.path.getsize(t_path) == 0:
            template_name = '遊戲頁.html'
    except:
        template_name = '遊戲頁.html'

    extra = {}
    if p_type == 'lis':
        extra['lis_question'] = q.get('lis_question', '')
        audio_text = q.get('q', '')
        if tts_service and audio_text:
            extra['audio_url'] = tts_service.generate(audio_text) or ''
        else:
            extra['audio_url'] = ''

    return render_template(template_name,
                           question=q['q'],
                           options=q['o'],
                           current_idx=idx,
                           total=len(questions),
                           quiz_type=q['type'],
                           player_score=session.get('score', 0),
                           bot_score=session.get('bot_score', 0),
                           last_points=last_points,
                           last_correct=last_correct,
                           **extra)

@app.route('/answer', methods=['POST'])
def answer():
    user_ans = request.form.get('answer', '')
    time_left = float(request.form.get('time_left', 0))
    idx = session.get('current_idx', 0)
    questions = session.get('questions', [])

    is_correct = False
    points_earned = 0

    if idx < len(questions):
        correct_ans = questions[idx]['a']
        if user_ans and user_ans == correct_ans:
            is_correct = True
            points_earned = max(100, round(1000 * time_left / 8))
            session['score'] = session.get('score', 0) + points_earned
            session['correct_count'] = session.get('correct_count', 0) + 1
        # Simulate bot: 60% correct, answers at random time 1–7s
        bot_time = random.uniform(1, 7)
        bot_correct = random.random() < 0.6
        bot_pts = max(100, round(1000 * bot_time / 8)) if bot_correct else 0
        session['bot_score'] = session.get('bot_score', 0) + bot_pts
        session['current_idx'] = idx + 1

    return redirect(url_for('quiz', lp=points_earned, lc=1 if is_correct else 0))

@app.route('/result')
def result():
    score = session.get('score', 0)
    correct_count = session.get('correct_count', 0)
    bot_score = session.get('bot_score', 0)
    total = len(session.get('questions', []))
    accuracy = int((correct_count / total) * 100) if total > 0 else 0
    return render_template('獲勝介面.html',
                           user_name="英雄玩家",
                           score=score,
                           bot_score=bot_score,
                           total=total,
                           correct=correct_count,
                           wrong=total - correct_count,
                           accuracy=accuracy)

@app.route('/start_game_lobby')
def start_game_lobby():
    level = request.args.get('level', 'A1A2')
    category = request.args.get('category', 'mixed')

    questions = []
    for _ in range(5):
        q = None
        if category == 'vocabulary':
            q = generate_word_quiz()
        elif category == 'grammar':
            q = generate_grammar_quiz()
        else:
            q = generate_word_quiz() if random.choice([True, False]) else generate_grammar_quiz()
        if q:
            questions.append(q)

    session['questions'] = questions
    session['current_idx'] = 0
    session['score'] = 0
    session['correct_count'] = 0
    session['bot_score'] = 0
    session['p_type'] = None
    return redirect(url_for('quiz'))

# ==================== Admin Routes ====================

@app.route('/admin/questions')
def admin_questions():
    return render_template('admin_questions.html')

@app.route('/admin/content')
def admin_content():
    return render_template('admin_content.html')

# ==================== Content API ====================

@app.route('/api/content/<topic>/<content_type>', methods=['GET'])
def api_get_content(topic, content_type):
    if content_service is None:
        return jsonify({'error': 'Service not available'}), 503
    items = content_service.get_items(topic, content_type)
    return jsonify({'items': items, 'total': len(items)})

@app.route('/api/content/<topic>/<content_type>', methods=['POST'])
def api_add_content(topic, content_type):
    if content_service is None:
        return jsonify({'error': 'Service not available'}), 503
    data = request.get_json()
    item = content_service.add_item(topic, content_type, data)
    if item is None:
        return jsonify({'error': 'Invalid topic or content type'}), 400
    return jsonify(item), 201

@app.route('/api/content/<topic>/<content_type>/<item_id>', methods=['GET'])
def api_get_content_item(topic, content_type, item_id):
    if content_service is None:
        return jsonify({'error': 'Service not available'}), 503
    item = content_service.get_item(topic, content_type, item_id)
    if item is None:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(item)

@app.route('/api/content/<topic>/<content_type>/<item_id>', methods=['PUT'])
def api_update_content(topic, content_type, item_id):
    if content_service is None:
        return jsonify({'error': 'Service not available'}), 503
    data = request.get_json()
    item = content_service.update_item(topic, content_type, item_id, data)
    if item is None:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(item)

@app.route('/api/content/<topic>/<content_type>/<item_id>', methods=['DELETE'])
def api_delete_content(topic, content_type, item_id):
    if content_service is None:
        return jsonify({'error': 'Service not available'}), 503
    success = content_service.delete_item(topic, content_type, item_id)
    if not success:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'success': True})

# ==================== API Routes ====================

@app.route('/api/questions', methods=['GET'])
def api_get_questions():
    if question_service is None:
        return jsonify({'error': 'Service not available'}), 503
    page = int(request.args.get('page', 1))
    level = request.args.get('level') or None
    topic = request.args.get('topic') or None
    q_type = request.args.get('type') or None
    search = request.args.get('search') or None
    result = question_service.get_all_manual_questions(
        page=page, per_page=10,
        search=search, level=level, topic=topic, q_type=q_type
    )
    return jsonify(result)

@app.route('/api/questions', methods=['POST'])
def api_create_question():
    if question_service is None:
        return jsonify({'error': 'Service not available'}), 503
    data = request.get_json()
    question = question_service.add_question(data)
    return jsonify(question), 201

@app.route('/api/questions/<question_id>', methods=['GET'])
def api_get_question(question_id):
    if question_service is None:
        return jsonify({'error': 'Service not available'}), 503
    question = question_service.get_question_by_id(question_id)
    if question is None:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(question)

@app.route('/api/questions/<question_id>', methods=['PUT'])
def api_update_question(question_id):
    if question_service is None:
        return jsonify({'error': 'Service not available'}), 503
    data = request.get_json()
    question = question_service.update_question(question_id, data)
    if question is None:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(question)

@app.route('/api/questions/<question_id>', methods=['DELETE'])
def api_delete_question(question_id):
    if question_service is None:
        return jsonify({'error': 'Service not available'}), 503
    success = question_service.delete_question(question_id)
    if not success:
        return jsonify({'error': 'Not found'}), 404
    return jsonify({'success': True})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    load_data()
    print("🎮 華語知識王伺服器啟動中...")
    print("📱 訪問 http://localhost:5000 開始遊戲")
    app.run(debug=True, port=5000, host='0.0.0.0')
