# ============================================================
# ИНТЕРФЕЙС ПРИЛОЖЕНИЯ
# ============================================================
import contextlib
import io
import random as rnd
import time

import pandas as pd
import streamlit as st

from db.user import add_personal_word, delete_personal_word, get_user_words, get_personal_words
from db.user import get_statistics, update_stats, render_schema

from streamlit.runtime.scriptrunner_utils.exceptions import RerunException
from streamlit.runtime.scriptrunner_utils.script_requests import RerunData


def render_sidebar():
    """
    TODO: Реализовать боковую панель с авторизацией
    - Поле для ввода имени
    - Кнопка входа
    - Приветствие после входа
    - Кнопка выхода
    """

    st.sidebar.title("Профиль")
    is_auth = st.session_state.get("is_auth", False)
    if is_auth:
        username = st.session_state.get("username", "Гость")
        st.sidebar.success(f"✅ Привет, {username}!")
        if st.sidebar.button("Выйти"):
            st.session_state["is_auth"] = False
            st.session_state["user_id"] = None
            raise RerunException(RerunData())
    else:
        st.sidebar.info("🔑 Введите имя для входа")
        with st.sidebar.form("login_form"):
            username = st.text_input("Имя пользователя")
            submit = st.form_submit_button("Войти")
            return {"submit": submit, "username": username}
    return None


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================
#  Функция генерации вариантов ответов
def generate_options(correct_word, all_words):
    """
    TODO: Сгенерировать 4 варианта ответа для викторины
    Один вариант - правильный перевод, остальные - случайные слова из словаря
    Если слов не хватает, можно добавить слова-заглушки
    """
    dummy_words = ["слово1", "слово2", "слово3", "слово4", "слово5"]
    options_pool = [word.get('english_word') for word in all_words
                    if word.get('english_word') != correct_word]
    needed = 3 - len(options_pool)
    if needed > 0:
        options_pool += dummy_words[:needed]
    options = rnd.sample(options_pool, 3)
    options.append(correct_word)
    rnd.shuffle(options)
    return options


#  Функция отображения схемы БД
def capture_render_schema():
    """
    Вызывает render_schema() и перехватывает её вывод (stdout) в строку.
    """
    buffer = io.StringIO()

    with contextlib.redirect_stdout(buffer):
        result = render_schema()

    captured_output = buffer.getvalue()
    return result if result is not None else captured_output


# ============================================================
# ОСНОВНЫЕ ФУНКЦИИ
# ============================================================
# Главная страница
def render_study_tab():
    """
    TODO: Реализовать вкладку изучения слов
    - Отображение текущего слова на русском
    - 4 кнопки с вариантами перевода
    - Обработка правильных/неправильных ответов
    - Кнопка следующего слова
    - Каждая порция - 4 случайных слова,
    новые порции загружаются после прохождения текущей.
    """

    if 'current_batch' not in st.session_state:
        st.session_state.current_batch = (
            get_user_words(st.session_state.user_id)
        )
        st.session_state.current_index = 0
        st.session_state.options = []
        st.session_state.correct_answers = 0
        st.session_state.wrong_answers = 0

    batch = st.session_state.current_batch
    if not batch:
        st.warning("Ваша база слов пуста. "
                   "Добавьте слова на вкладке '➕ Добавить слово'.")
        return

    if st.session_state.current_index >= len(batch):
        st.session_state.current_index = 0

    current_index = st.session_state.current_index
    current_word = batch[current_index]
    russian_word = current_word['russian_word']
    correct_english = current_word['english_word']
    word_id = current_word['id']
    word_type = current_word['word_type']

    if not st.session_state.options:
        st.session_state.options = generate_options(correct_english, batch)

    options = st.session_state.options

    st.markdown(f"### 📖 Изучаем слово {current_index + 1} "
                f"из {len(batch)} в текущем блоке")
    st.subheader(f"Как будет по-английски слово: **{russian_word}**?")

    with st.form(key="study_form"):
        cols = st.columns(4)
        buttons = []
        for i, opt in enumerate(options):
            with cols[i]:
                buttons.append(st.form_submit_button(opt, key=f"opt_{i}"))
        skip = st.form_submit_button("⏩ Пропустить слово", type="secondary")

    # Обработка выбора пользователя
    user_choice = None
    for i, btn in enumerate(buttons):
        if btn:
            user_choice = options[i]
            break

    if user_choice is not None:
        # Выбран вариант ответа
        if user_choice == correct_english:
            st.success("✅ Верно!")
            st.session_state.correct_answers += 1
            update_stats(
                user_id=st.session_state.user_id,
                word_id=word_id,
                word_type=word_type,
                is_correct=True
            )
            st.balloons()
            # Переход к следующему слову или новой порции
            next_index = current_index + 1
            if next_index < len(batch):
                st.session_state.current_index = next_index
                st.session_state.options = []
            else:
                st.info(
                    "Поздравляем! Вы прошли текущий блок. "
                    "Загружаем следующий..."
                )
                time.sleep(3)
                st.session_state.current_batch = (
                    get_user_words(st.session_state.user_id)
                )
                st.session_state.current_index = 0
                st.session_state.options = []
            st.rerun()
        else:
            st.error(f"❌ Неверно. Правильный ответ: {correct_english}")
            st.session_state.wrong_answers += 1
            update_stats(
                user_id=st.session_state.user_id,
                word_id=word_id,
                word_type=word_type,
                is_correct=False
            )
            # Остаёмся на том же слове, варианты не сбрасываем
            st.rerun()
    elif skip:
        next_index = current_index + 1
        if next_index < len(batch):
            st.session_state.current_index = next_index
            st.session_state.options = []
        else:
            st.session_state.current_batch = (
                get_user_words(st.session_state.user_id)
            )
            st.session_state.current_index = 0
            st.session_state.options = []
        st.rerun()

    # Отображение текущей статистики сессии
    st.metric(
        "✅ Правильных ответов (сессия)",
        st.session_state.correct_answers
    )
    st.metric(
        "❌ Неправильных ответов (сессия)",
        st.session_state.wrong_answers
    )


# Страница добавления слова
def render_add_word_tab():
    """
    Вкладка добавления персонального слова.
    """
    st.info("Добавьте русское слово и его перевод на английский язык ➕")

    # Отображение сохранённых сообщений (после rerun)
    if st.session_state.get("add_success_msg"):
        st.success(st.session_state.add_success_msg)
        st.session_state.add_success_msg = None
    if st.session_state.get("add_error_msg"):
        st.error(st.session_state.add_error_msg)
        st.session_state.add_error_msg = None

    # Очистка полей по флагу (перед созданием виджетов)
    if st.session_state.get("clear_add_form", False):
        st.session_state.new_russian = ""
        st.session_state.new_english = ""
        st.session_state.clear_add_form = False

    # Инициализация значений полей (если ещё нет)
    if "new_russian" not in st.session_state:
        st.session_state.new_russian = ""
    if "new_english" not in st.session_state:
        st.session_state.new_english = ""

    with st.form("add_word_form"):
        russian_word = st.text_input(
            "Русское слово", key="new_russian"
        ).strip()
        english_word = st.text_input(
            "Перевод на английский язык", key="new_english"
        ).strip()
        is_submitted = st.form_submit_button("Добавить")

    if is_submitted:
        if not russian_word or not english_word:
            st.warning("⚠️ Пожалуйста, заполните оба поля перед добавлением.")
        else:
            success = add_personal_word(
                st.session_state.user_id, russian_word, english_word
            )
            if success is True:
                st.session_state.add_success_msg = (
                    f"✅ Слово **{russian_word}** "
                    f"→ **{english_word}** добавлено!"
                )
                st.session_state.clear_add_form = True
                st.rerun()
            elif success is False:
                st.session_state.add_error_msg = (
                    f"❌ Слово **{russian_word}** уже есть в вашем словаре."
                )
                st.session_state.clear_add_form = True
                st.rerun()
            else:
                st.session_state.add_error_msg = \
                    "⚠️ Произошла непредвиденная ошибка."
                st.rerun()


# Страница удаления слова
def render_delete_word_tab():
    """
    TODO: Реализовать вкладку удаления слова
    - Выпадающий список с персональными словами пользователя
    - Кнопка удаления
    - Подтверждение удаления
    """
    user_id = st.session_state.user_id
    words = get_personal_words(user_id)

    if 'show_confirm' not in st.session_state:
        st.session_state.show_confirm = False
    if 'word_to_delete' not in st.session_state:
        st.session_state.word_to_delete = None
    if 'delete_in_progress' not in st.session_state:
        st.session_state.delete_in_progress = False
    if 'delete_error' not in st.session_state:
        st.session_state.delete_error = None
    if 'success_message' not in st.session_state:
        st.session_state.success_message = None

    # Отображение успешного сообщения, если есть
    if st.session_state.success_message:
        st.success(st.session_state.success_message)
        st.session_state.success_message = None

    # Отображение ошибки, если есть
    if st.session_state.delete_error:
        st.error(st.session_state.delete_error)
        st.session_state.delete_error = None

    st.info("Вы можете 🗑️ удалить любое слово, которое ранее добавили.")

    if not words:
        st.info("У вас пока нет добавленных слов.")
        return

    word_options = {f"{word['russian_word']} (ID: {word['id']})":
                    word for word in words}
    widget_key = "_".join(sorted(str(w['id']) for w in words))

    selected_option = st.selectbox(
        "Выберите слово из выпадающего списка",
        options=[""] + list(word_options.keys()),
        key=widget_key
    )

    delete_button_visible = (bool(
        selected_option)
        and not st.session_state.show_confirm
        and not st.session_state.delete_in_progress)

    if delete_button_visible and st.button("Удалить выбранное слово"):
        st.session_state.word_to_delete = word_options[selected_option]
        st.session_state.show_confirm = True

    if (st.session_state.show_confirm
            and not st.session_state.delete_in_progress):
        st.warning(
            f"Вы собираетесь удалить слово: "
            f"**{st.session_state.word_to_delete['russian_word']}**. "
            f"Это действие необратимо.")

        if st.button("Подтвердить удаление"):
            st.session_state.delete_in_progress = True
            st.rerun()

        if st.button("Отмена"):
            st.session_state.show_confirm = False
            st.session_state.word_to_delete = None
            st.rerun()

    if (st.session_state.delete_in_progress
            and st.session_state.word_to_delete):
        with st.spinner(
                f"Удаляется слово "
                f"'{st.session_state.word_to_delete['russian_word']}'"
        ):
            try:
                user_id = st.session_state.user_id
                word_id = st.session_state.word_to_delete['id']
                success = delete_personal_word(user_id, word_id)
                if success:
                    st.session_state.success_message = "Слово успешно удалено!"
                else:
                    raise Exception("Функция удаления вернула False. "
                                    "Не удалось выполнить операцию.")
            except Exception as e:
                st.error(f"Произошла ошибка при удалении: {e}")
            finally:
                st.session_state.show_confirm = False
                st.session_state.word_to_delete = None
                st.session_state.delete_in_progress = False
            st.rerun()


# Страница статистики
def render_statistics_tab(user_id):
    """
    TODO: Реализовать вкладку статистики (дополнительное требование)
    - Количество изученных слов
    - Количество попыток
    - Процент правильных ответов
    - История последних попыток
    """
    st.title("Ваша статистика обучения")
    st.write("Здесь вы можете увидеть свой прогресс и последние результаты.")

    st.subheader("Ключевые показатели")
    col1, col2 = st.columns(2)
    stats = get_statistics(user_id)

    if stats is None:
        st.error("Произошла ошибка при загрузке вашей статистики.")
        return

    with col1:
        total_attempts = stats.get('total_attempts', 0)
        st.metric(label="Всего попыток", value=total_attempts)
        learned_words_count = stats.get('learned_words_count', 0)
        st.metric(label="Изучено слов", value=learned_words_count)

    with ((((col2)))):
        avg_accuracy = stats.get('avg_accuracy_percent')
        accuracy_value = (
            f"{avg_accuracy}%" if avg_accuracy is not None else "Нет данных"
        )
        st.metric(label="Точность ответов", value=accuracy_value)

    st.divider()

    st.subheader("История последних попыток")

    history_df = None

    if stats:
        words_history = stats.get('last_reviewed_words', [])
        if words_history:
            history_df = pd.DataFrame(words_history)
            history_df = history_df.rename(columns={
                'word_id': 'ID слова',
                'russian_word': 'Слово',
                'english_word': 'Перевод',
                'word_type': 'Тип',
                'correct_answers': 'Результат',
                'last_reviewed': 'Дата'
            })

            history_df = history_df[[
                'ID слова',
                'Слово',
                'Перевод',
                'Тип',
                'Результат',
                'Дата'
            ]]

            history_df['Результат'] = history_df['Результат'].map({
                True: '✅ Правильно',
                False: '❌ Ошибка'
            })

            history_df['Дата'] = (
                pd.to_datetime(history_df['Дата'], errors='coerce')
                .dt.strftime('%Y-%m-%d %H:%M:%S')
            )
        else:
            history_df = pd.DataFrame(columns=[
                'ID слова', 'Слово', 'Перевод', 'Тип', 'Результат', 'Дата'
            ])
    else:
        history_df = pd.DataFrame(columns=[
            'ID слова', 'Слово', 'Перевод', 'Тип', 'Результат', 'Дата'
        ])

    if history_df is not None and not history_df.empty:
        st.dataframe(history_df, width='stretch')
    else:
        st.info("Пока нет данных о попытках. "
                "Начните обучение, чтобы увидеть здесь свою историю!")
