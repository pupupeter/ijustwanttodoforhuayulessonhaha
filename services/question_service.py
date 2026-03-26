import json
import random
import os
import pandas as pd
from typing import List, Optional
from datetime import datetime
import uuid

class QuestionService:
    # A2-B1 level mapping based on Excel ji column
    LEVEL_FILTER = {
        'A2': ['第2*級', '第2級'],
        'B1': ['第3*級', '第3級', '第4*級', '第4級'],
        'all': ['第2*級', '第2級', '第3*級', '第3級', '第4*級', '第4級']
    }

    def __init__(self, word_file: str, grammar_file: str, manual_questions_file: str):
        self.word_file = word_file
        self.grammar_file = grammar_file
        self.manual_questions_file = manual_questions_file
        self.df_word = None
        self.df_grammar = None
        self.manual_questions = {'questions': []}
        self.load_data()

    def load_data(self):
        try:
            self.df_word = pd.read_excel(self.word_file)
            print(f"Loaded {len(self.df_word)} words from Excel")
        except Exception as e:
            print(f"Failed to load word file: {e}")

        try:
            self.df_grammar = pd.read_excel(self.grammar_file)
            print(f"Loaded {len(self.df_grammar)} grammar points from Excel")
        except Exception as e:
            print(f"Failed to load grammar file: {e}")

        self.load_manual_questions()

    def load_manual_questions(self):
        try:
            if os.path.exists(self.manual_questions_file):
                with open(self.manual_questions_file, 'r', encoding='utf-8') as f:
                    self.manual_questions = json.load(f)
                print(f"Loaded {len(self.manual_questions.get('questions', []))} manual questions")
        except Exception as e:
            print(f"Failed to load manual questions: {e}")
            self.manual_questions = {'questions': []}

    def save_manual_questions(self):
        try:
            with open(self.manual_questions_file, 'w', encoding='utf-8') as f:
                json.dump(self.manual_questions, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Failed to save manual questions: {e}")
            return False

    def filter_words_by_level(self, level: str = 'all') -> pd.DataFrame:
        if self.df_word is None:
            return pd.DataFrame()

        level_values = self.LEVEL_FILTER.get(level, self.LEVEL_FILTER['all'])
        filtered = self.df_word[self.df_word['ji'].isin(level_values)]
        return filtered

    def generate_word_quiz(self, level: str = 'all', topic: str = 'all') -> Optional[dict]:
        df_filtered = self.filter_words_by_level(level)
        if df_filtered.empty:
            return None

        target = df_filtered.sample(n=1).iloc[0]
        word = target['word']
        correct_pinyin = target['pinyin']

        # Get distractors from same level
        distractors_df = df_filtered[df_filtered['word'] != word]
        if len(distractors_df) < 3:
            distractors_df = self.df_word[self.df_word['word'] != word]

        distractors = distractors_df.sample(n=min(3, len(distractors_df)))['pinyin'].tolist()

        options = [
            {'id': 'A', 'text': correct_pinyin, 'is_correct': True},
        ]
        for i, d in enumerate(distractors):
            options.append({'id': chr(66 + i), 'text': d, 'is_correct': False})

        random.shuffle(options)
        for i, opt in enumerate(options):
            opt['id'] = chr(65 + i)

        return {
            'id': f'excel_{uuid.uuid4().hex[:8]}',
            'type': 'vocabulary',
            'level': level,
            'topic': topic,
            'question': {
                'text': f'請問詞語「{word}」的拼音是什麼？',
                'audio_text': None
            },
            'options': options,
            'source': 'excel'
        }

    def generate_grammar_quiz(self, level: str = 'all') -> Optional[dict]:
        if self.df_grammar is None:
            return None

        filtered = self.df_grammar[self.df_grammar['例句'].notna()]
        if filtered.empty:
            return None

        target = filtered.sample(n=1).iloc[0]
        gp = str(target['語法點'])
        sent = str(target['例句'])

        if gp in sent:
            q_text = sent.replace(gp, "___", 1)
        else:
            q_text = f"請將「{gp}」填入正確位置：\n{sent}"

        distractors_df = self.df_grammar[self.df_grammar['語法點'] != gp]
        distractors = distractors_df.sample(n=min(3, len(distractors_df)))['語法點'].tolist()

        options = [
            {'id': 'A', 'text': gp, 'is_correct': True},
        ]
        for i, d in enumerate(distractors):
            options.append({'id': chr(66 + i), 'text': str(d), 'is_correct': False})

        random.shuffle(options)
        for i, opt in enumerate(options):
            opt['id'] = chr(65 + i)

        return {
            'id': f'grammar_{uuid.uuid4().hex[:8]}',
            'type': 'dialogue',
            'level': level,
            'topic': 'all',
            'question': {
                'text': q_text,
                'audio_text': None
            },
            'options': options,
            'source': 'excel'
        }

    def get_manual_questions(self, level: str = 'all', topic: str = 'all',
                            q_type: str = 'all') -> List[dict]:
        questions = self.manual_questions.get('questions', [])

        filtered = []
        for q in questions:
            if level != 'all' and q.get('level') != level:
                continue
            if topic != 'all' and q.get('topic') != topic:
                continue
            if q_type != 'all' and q.get('type') != q_type:
                continue
            filtered.append(q)

        return filtered

    def generate_mixed_questions(self, count: int = 5, level: str = 'all',
                                 topic: str = 'all') -> List[dict]:
        questions = []
        manual_qs = self.get_manual_questions(level, topic)

        # Try to include some manual questions if available
        manual_count = min(len(manual_qs), count // 2)
        if manual_count > 0:
            questions.extend(random.sample(manual_qs, manual_count))

        # Fill remaining with Excel questions
        remaining = count - len(questions)
        for _ in range(remaining):
            if random.choice([True, False]):
                q = self.generate_word_quiz(level, topic)
            else:
                q = self.generate_grammar_quiz(level)
            if q:
                questions.append(q)

        random.shuffle(questions)
        return questions

    # CRUD operations for manual questions
    def add_question(self, question_data: dict) -> dict:
        question_id = f'manual_{uuid.uuid4().hex[:8]}'
        question = {
            'id': question_id,
            'type': question_data.get('type', 'vocabulary'),
            'level': question_data.get('level', 'A2'),
            'topic': question_data.get('topic', 'all'),
            'question': {
                'text': question_data.get('question_text', ''),
                'audio_text': question_data.get('audio_text')
            },
            'options': question_data.get('options', []),
            'created_at': datetime.now().isoformat()
        }
        self.manual_questions['questions'].append(question)
        self.save_manual_questions()
        return question

    def update_question(self, question_id: str, question_data: dict) -> Optional[dict]:
        questions = self.manual_questions.get('questions', [])
        for i, q in enumerate(questions):
            if q['id'] == question_id:
                q['type'] = question_data.get('type', q['type'])
                q['level'] = question_data.get('level', q['level'])
                q['topic'] = question_data.get('topic', q['topic'])
                q['question']['text'] = question_data.get('question_text', q['question']['text'])
                q['question']['audio_text'] = question_data.get('audio_text', q['question'].get('audio_text'))
                q['options'] = question_data.get('options', q['options'])
                q['updated_at'] = datetime.now().isoformat()
                self.save_manual_questions()
                return q
        return None

    def delete_question(self, question_id: str) -> bool:
        questions = self.manual_questions.get('questions', [])
        for i, q in enumerate(questions):
            if q['id'] == question_id:
                questions.pop(i)
                self.save_manual_questions()
                return True
        return False

    def get_question_by_id(self, question_id: str) -> Optional[dict]:
        questions = self.manual_questions.get('questions', [])
        for q in questions:
            if q['id'] == question_id:
                return q
        return None

    def get_all_manual_questions(self, page: int = 1, per_page: int = 10,
                                  search: str = None, level: str = None,
                                  topic: str = None, q_type: str = None) -> dict:
        questions = self.manual_questions.get('questions', [])

        # Filter
        filtered = []
        for q in questions:
            if level and q.get('level') != level:
                continue
            if topic and q.get('topic') != topic:
                continue
            if q_type and q.get('type') != q_type:
                continue
            if search:
                search_lower = search.lower()
                q_text = q.get('question', {}).get('text', '').lower()
                if search_lower not in q_text:
                    continue
            filtered.append(q)

        # Paginate
        total = len(filtered)
        start = (page - 1) * per_page
        end = start + per_page
        paginated = filtered[start:end]

        return {
            'questions': paginated,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }
