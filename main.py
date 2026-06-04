"""
EnglishCard - Приложение для изучения английского языка
"""
import streamlit as st
from streamlit.runtime.scriptrunner import RerunException, RerunData
from db.init_db import init_database
from db.user import get_user_words, login_user, get_personal_words
from ui.sidebar import render_sidebar, render_study_tab, render_add_word_tab
from ui.sidebar import render_statistics_tab, render_delete_word_tab


# ============================================================
# НАСТРОЙКА СТРАНИЦЫ
# ============================================================
st.set_page_config(
    page_title="EnglishCard - Изучение английского",
    page_icon="📚",
    layout="wide"
)
st.title("📚 EnglishCard - Изучай английский с удовольствием!")


# ============================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================
def main():
    """
    Главная функция приложения
    Реализовать основную логику:
    1. Инициализация БД
    2. Авторизация пользователя
    3. Отображение вкладок с функционалом
    4. Приветственное сообщение для неавторизованных пользователей
    """

    # Инициализация состояния сессии
    if "is_auth" not in st.session_state:
        st.session_state.is_auth = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "username" not in st.session_state:
        st.session_state.username = ""

    # Инициализация БД
    init_database()

    # Боковая панель с авторизацией
    form_data = render_sidebar()
    if form_data and form_data["submit"]:
        username = form_data["username"].strip()
        if username:
            user_id = login_user(username)

            if user_id is not None:
                st.session_state["is_auth"] = True
                st.session_state["username"] = username
                st.session_state["user_id"] = user_id
                raise RerunException(RerunData())
            else:
                st.sidebar.error("Произошла ошибка. Попробуйте другое имя.")

    # Основной контент в зависимости от авторизации
    if 'user_id' in st.session_state and st.session_state.user_id:
        user_id = st.session_state.user_id
        try:
            words = get_user_words(user_id)
            personal_words = get_personal_words(user_id)
        except Exception as e:
            st.error(f"Не удалось загрузить ваши данные. "
                     f"Попробуйте перезагрузить страницу. ({e})")
            st.stop()

        tab1, tab2, tab3, tab4 = st.tabs(
            ["📖 Изучение",
             "➕ Добавить слово",
             "🗑️ Удалить слово",
             "📊 Статистика"
             ])
        with tab1:
            render_study_tab(words)
        with tab2:
            render_add_word_tab()
        with tab3:
            render_delete_word_tab(personal_words)
        with tab4:
            render_statistics_tab(user_id)
    else:
        st.title("Тренажер словарного запаса")
        st.markdown("Привет 👋 Давай попрактикуемся в английском языке.")
        st.markdown("Тренировки можешь проходить в удобном для себя темпе.")
        st.markdown("")
        st.markdown("У тебя есть возможность использовать тренажёр, "
                    "как конструктор, и собирать свою собственную базу "
                    "для обучения")
        st.markdown("Для этого воспользуйся инструментами:")
        st.markdown("- добавить слово ➕,")
        st.markdown("- удалить слово 🗑️.")
        st.markdown("")
        st.markdown("Ну что, начнём ⬇️")
        st.info("Авторизуйся в боковой панели, чтобы начать.")

    st.divider()
    st.caption("Приложение для изучения английских слов. 2026 Останин КЮ")


if __name__ == "__main__":
    main()
