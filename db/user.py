from db.init_db import get_db_connection
from tabulate import tabulate


def login_user(username):
    """
    TODO: Реализовать вход пользователя
    Если пользователь существует - вернуть его id
    Если нет - создать нового и вернуть его id
    """

    if not username.strip():
        print("Попытка входа с пустым именем.")
        return None

    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        result = cur.fetchone()
        if result is not None:
            user_id = result[0]
            print(f"Пользователь '{username}' найден. ID: {user_id}")
            return user_id
        else:
            print(f"Пользователь '{username}' не найден. Создаем нового...")
            cur.execute(
                "INSERT INTO users (username) VALUES (%s) RETURNING id",
                (username,)
            )
            user_id = cur.fetchone()[0]
            conn.commit()
            print(f"Новый пользователь создан. ID: {user_id}")
            return user_id
    except Exception as e:
        print(f"Ошибка при работе с базой данных: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def get_user_words(user_id):
    """
    TODO: Получить все слова пользователя (общие + персональные)
    Возвращает список словарей:
    [{'id': 1,
    'russian_word': 'красный',
    'english_word': 'red',
    'word_type': 'common'}, ...]
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, russian_word, english_word, 'common' AS word_type
            FROM common_words
            UNION ALL
            SELECT id, russian_word, english_word, 'personal' AS word_type
            FROM user_words
            WHERE user_id = %s;
        """, (user_id,))
        rows = cur.fetchall()
        word_list = []
        for row in rows:
            word_dict = {
                "id": row[0],
                "russian_word": row[1],
                "english_word": row[2],
                'word_type': row[3]
            }
            word_list.append(word_dict)
        return word_list or []
    except Exception as e:
        print(f"Ошибка при получении слов пользователя {user_id}: {e}")
        return []
    finally:
        conn.close()


def add_personal_word(user_id, russian_word, english_word):
    """
    TODO: Добавить персональное слово для пользователя
    Проверить, нет ли уже такого слова
    Возвращает True/False
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
                SELECT russian_word
                FROM common_words
                UNION ALL
                SELECT russian_word
                FROM user_words
                WHERE user_id = %s;
        """, (user_id,))
        rows = cur.fetchall()
        unique_words = [word[0] for word in rows]
        if russian_word not in unique_words:
            cur.execute("""
                INSERT INTO user_words (user_id, russian_word, english_word)
                VALUES (%s, %s, %s)
            """, (user_id, russian_word, english_word))
            conn.commit()
            return True
        else:
            return False
    except Exception as e:
        print(f"Ошибка при добавлении слова: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def get_personal_words(user_id):
    """
    TODO: Получить все слова пользователя (персональные)
    Возвращает список словарей:
    [{'id': 1,
    'russian_word': 'красный',
    'english_word': 'red',
    'word_type': 'common'}, ...]
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
                SELECT id, russian_word, english_word, 'personal' AS word_type
                FROM user_words
                WHERE user_id = %s;
            """, (user_id,))
        rows = cur.fetchall()
        word_list = []
        for row in rows:
            word_dict = {
                "id": row[0],
                "russian_word": row[1],
                "english_word": row[2],
                'word_type': row[3]
            }
            word_list.append(word_dict)
        return word_list or []
    except Exception as e:
        print(f"Ошибка при получении слов пользователя {user_id}: {e}")
        return []
    finally:
        conn.close()


def delete_personal_word(user_id, word_id):
    """
    TODO: Удалить персональное слово пользователя
    Возвращает True/False
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
                SELECT id
                FROM user_words
                WHERE id = %s AND user_id = %s;
            """, (word_id, user_id))
        if not cur.fetchone():
            return False
        cur.execute("""
                DELETE FROM user_words
                WHERE id = %s AND user_id = %s;
            """, (word_id, user_id))
        conn.commit()
        return cur.rowcount > 0
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при удалении слова: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def update_stats(user_id, word_id, word_type, is_correct):
    """
    TODO: Обновить статистику изучения слова
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
                INSERT INTO learning_stats (
                    user_id,
                    word_id,
                    word_type,
                    correct_answers,
                    total_attempts,
                    last_reviewed
                    )
                VALUES (%s, %s, %s, %s, 1, NOW());
            """, (user_id, word_id, word_type, is_correct))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Ошибка при обновлении статистики: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def get_statistics(user_id):
    """
    Получает статистику пользователя и список последних 20 изученных слов.
    Возвращает словарь с агрегированными данными и историей.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            WITH user_stats AS (
                SELECT
                    SUM(total_attempts) AS total_attempts,
                    SUM(CASE WHEN correct_answers THEN 1 ELSE 0 END)
                        AS total_correct
                FROM learning_stats
                WHERE user_id = %s
            ),
            learned_user_words AS (
                SELECT COUNT(DISTINCT ls.word_id) AS count
                FROM learning_stats ls
                JOIN user_words uw ON ls.word_id = uw.id AND uw.user_id = %s
                WHERE ls.user_id = %s
            ),
            learned_common_words AS (
                SELECT COUNT(DISTINCT ls.word_id) AS count
                FROM learning_stats ls
                JOIN common_words cw ON ls.word_id = cw.id
                WHERE ls.user_id = %s
            )
            SELECT
                ls.word_id,
                CASE ls.word_type
                    WHEN 'personal' THEN uw.russian_word
                    ELSE cw.russian_word
                END AS russian_word,
                CASE ls.word_type
                    WHEN 'personal' THEN uw.english_word
                    ELSE cw.english_word
                END AS english_word,
                ls.word_type,
                ls.correct_answers,
                ls.total_attempts,
                ls.last_reviewed,
                us.total_attempts AS stats_total_attempts,
                us.total_correct AS stats_total_correct,
                (SELECT count FROM learned_user_words)
                    + (SELECT count FROM learned_common_words)
                    AS stats_unique_words_count
            FROM learning_stats ls
            LEFT JOIN user_words uw ON ls.word_id = uw.id AND uw.user_id = %s
            LEFT JOIN common_words cw ON ls.word_id = cw.id
            CROSS JOIN user_stats us
            WHERE ls.user_id = %s
            ORDER BY ls.last_reviewed DESC
            LIMIT 20;
        """, (user_id, user_id, user_id, user_id, user_id, user_id))

        rows = cur.fetchall()
        if not rows:
            return {
                "total_attempts": 0,
                "total_correct": 0,
                "avg_accuracy_percent": None,
                "learned_words_count": 0,
                "last_reviewed_words": []
            }

        stats_row = rows[0]
        stats_total_attempts = stats_row[7]
        stats_total_correct = stats_row[8]
        stats_unique_words_count = stats_row[9]

        avg_accuracy_percent = None
        if stats_total_attempts and stats_total_attempts > 0:
            avg_accuracy_percent = round(
                (stats_total_correct / stats_total_attempts) * 100, 2
            )

        last_reviewed_words = []
        for row in rows:
            last_reviewed_words.append({
                "word_id": row[0],
                "russian_word": row[1],
                "english_word": row[2],
                "word_type": row[3],
                "correct_answers": row[4],
                "total_attempts": row[5],
                "last_reviewed": row[6]
            })

        return {
            "total_attempts": stats_total_attempts,
            "total_correct": stats_total_correct,
            "avg_accuracy_percent": avg_accuracy_percent,
            "learned_words_count": stats_unique_words_count,
            "last_reviewed_words": last_reviewed_words
        }

    except Exception as e:
        print(f"Ошибка при получении статистики: {e}")
        return None

    finally:
        cur.close()
        conn.close()


def render_schema():
    """
    Отображает схему базы данных PostgreSQL.
    Выводит список таблиц и их столбцов.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema='public' AND table_type='BASE TABLE';
    """)
    tables = [row[0] for row in cur.fetchall()]

    schema_info = []

    for table in tables:
        schema_info.append((f"Таблица: {table}", ""))
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = %s;
        """, (table,))
        columns = cur.fetchall()
        for col in columns:
            schema_info.append(
                ("", f"{col[0]} ({col[1]}) "
                     f"{'NOT NULL' if col[2] == 'NO' else ''}")
            )
    conn.close()
    return tabulate(
        schema_info,
        headers=["Объект", "Описание"],
        tablefmt="grid")
