# -*- coding: utf-8 -*-
"""
ГО-Карта: Обучение по Приказу МЧС №429
(c) 2025
"""

# --- Настройки приложения (ОБЯЗАТЕЛЬНО В НАЧАЛЕ) ---
import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import numpy as np
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
import json
import os

# --- Отладочный принт ---
st.write("✅ Приложение запущено!")

# --- Streamlit Configuration (MUST BE AT THE TOP)
st.set_page_config(
    page_title="🚨 ГО-Карта: Обучение по Приказу МЧС №429",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Состояние приложения ---
if 'accepted_terms' not in st.session_state:
    st.session_state['accepted_terms'] = False
if 'selected_district' not in st.session_state:
    st.session_state['selected_district'] = None
if 'show_memo' not in st.session_state:
    st.session_state['show_memo'] = None
if 'show_add_memo' not in st.session_state:
    st.session_state['show_add_memo'] = False
if 'show_add_building' not in st.session_state:
    st.session_state['show_add_building'] = False
if 'show_add_memorial' not in st.session_state:
    st.session_state['show_add_memorial'] = False
if 'show_memorials' not in st.session_state:
    st.session_state['show_memorials'] = False
if 'show_memorial_details' not in st.session_state:
    st.session_state['show_memorial_details'] = None
if 'user_location' not in st.session_state:
    st.session_state['user_location'] = None
if 'selected_emergency' not in st.session_state:
    st.session_state['selected_emergency'] = None
if 'closest_building' not in st.session_state:
    st.session_state['closest_building'] = None
if 'route_map' not in st.session_state:
    st.session_state['route_map'] = None

# --- Загрузка данных ---
@st.cache_data
def load_buildings_data():
    # Фиктивные данные для Ижевска
    data = {
        'id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'latitude': [56.8519, 56.8490, 56.8550, 56.8470, 56.8530, 56.8520, 56.8480, 56.8540, 56.8500, 56.8510],
        'longitude': [53.2013, 53.2100, 53.2050, 53.1990, 53.2070, 53.2020, 53.2040, 53.2090, 53.2000, 53.2030],
        'floors': [9, 5, 12, 3, 15, 4, 2, 8, 1, 20],
        'material': ['кирпич', 'панель', 'бетон', 'дерево', 'бетон', 'кирпич', 'металл', 'бетон', 'дерево', 'бетон'],
        'purpose': ['жилой дом', 'жилой дом', 'офис', 'жилой дом', 'торговый центр', 'школа', 'гараж', 'больница', 'гараж', 'офис'],
        'plan_link': [
            'https://via.placeholder.com/600x400/00ff00/000000?text=План+Эвакуации+1',
            'https://via.placeholder.com/600x400/00ff00/000000?text=План+Эвакуации+2',
            'https://via.placeholder.com/600x400/00ff00/000000?text=План+Эвакуации+3',
            'https://via.placeholder.com/600x400/00ff00/000000?text=План+Эвакуации+4',
            'https://via.placeholder.com/600x400/00ff00/000000?text=План+Эвакуации+5',
            'https://via.placeholder.com/600x400/00ff00/000000?text=План+Эвакуации+6',
            'https://via.placeholder.com/600x400/00ff00/000000?text=План+Эвакуации+7',
            'https://via.placeholder.com/600x400/00ff00/000000?text=План+Эвакуации+8',
            'https://via.placeholder.com/600x400/00ff00/000000?text=План+Эвакуации+9',
            'https://via.placeholder.com/600x400/00ff00/000000?text=План+Эвакуации+10'
        ]
    }
    df = pd.DataFrame(data)
    return df

@st.cache_data
def load_emergency_rules():
    # Реальные критерии из Приказа МЧС №429
    data = {
        'type_ru': [
            'Пожар', 'Наводнение', 'Ураган', 'Землетрясение', 'Авария на заводе',
            'Сильный снегопад', 'Сильный мороз', 'Сильная жара', 'Гололедица', 'Сход снежных лавин',
            'Лесные пожары', 'Биологические угрозы', 'Радиационные угрозы', 'Химические угрозы',
            'Авария на транспорте', 'Взрыв', 'Утечка опасных веществ', 'Загрязнение атмосферы'
        ],
        'description_ru': [
            'Возгорание в здании или на улице',
            'Подтопление местности',
            'Сильный ветер',
            'Толчки земли',
            'Утечка химикатов или авария на производстве',
            'Снегопад с интенсивностью 20 мм и более за 12 часов',
            'Температура воздуха ниже допустимой',
            'Температура воздуха выше допустимой',
            'Образование гололедицы на дорогах',
            'Сход снежных лавин, угроза населенным пунктам',
            'Распространение лесных пожаров',
            'Угроза инфекционным заболеваниям',
            'Утечка радиоактивных веществ',
            'Утечка химически опасных веществ',
            'Авария на транспорте (железнодорожном, автомобильном и т.д.)',
            'Взрыв, угроза жизни и здоровью',
            'Утечка опасных веществ, угроза жизни и здоровью',
            'Загрязнение атмосферы, угроза жизни и здоровью'
        ],
        'signs_ru': [
            'Запах дыма, огонь, сирены',
            'Вода на улице, подъём уровня',
            'Ветер >15 м/с, падение деревьев',
            'Дрожание зданий, треск',
            'Запах, пары, кашель, остановка производства',
            'Снег, метель, плохая видимость',
            'Очень низкая температура',
            'Очень высокая температура',
            'Скользкие дороги, падения',
            'Снежные массы, шум, разрушения',
            'Запах дыма, огонь в лесу',
            'Повышенное количество заболевших',
            'Аномальные показатели дозиметра',
            'Запах, пары, кашель, удушье',
            'Столкновение, сход с рельс, авария',
            'Громкий звук, вспышка, разрушения',
            'Запах, пары, кашель, удушье',
            'Запах, пары, кашель, удушье'
        ],
        'actions_ru': [
            'Покинуть здание, вызвать 112, не использовать лифт',
            'Отойти от воды, подняться выше, не пользоваться автомобилем',
            'Укрыться в помещении,远离 окон, не выходить',
            'Опуститься на корточки, укрыться, выйти наружу после',
            'Покинуть зону, использовать повязку, сообщить 112',
            'Оставайтесь дома, не выходите без необходимости, подготовьте припасы',
            'Оставайтесь в помещении, используйте обогрев, избегайте переохлаждения',
            'Оставайтесь в помещении, используйте кондиционер, пейте воду',
            'Будьте осторожны на улице, используйте противоскользящие накладки',
            'Немедленно покиньте зону угрозы, двигайтесь вверх по склону',
            'Сообщите в 112, отойдите от леса, не разводите костры',
            'Сообщите в 112, избегайте мест скопления людей, соблюдайте гигиену',
            'Немедленно покиньте зону, используйте защитные средства, сообщите 112',
            'Немедленно покиньте зону, используйте защитные средства, сообщите 112',
            'Сообщите в 112, окажите первую помощь, не трогайте пострадавших без необходимости',
            'Немедленно покиньте зону, используйте защитные средства, сообщите 112',
            'Немедленно покиньте зону, используйте защитные средства, сообщите 112',
            'Немедленно покиньте зону, используйте защитные средства, сообщите 112'
        ]
    }
    df = pd.DataFrame(data)
    return df

# --- Загрузка памяток ---
def load_memos():
    if os.path.exists('memos.json'):
        with open('memos.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Возвращаем пустой список, если файл не существует
        return []

# --- Загрузка данных в session_state ---
if 'buildings_df' not in st.session_state:
    st.session_state['buildings_df'] = load_buildings_data()

# Создаём папки images и videos, если их нет
os.makedirs("images", exist_ok=True)
os.makedirs("videos", exist_ok=True)

rules_df = load_emergency_rules()
memos = load_memos()

# --- Приветственное окно ---
if not st.session_state['accepted_terms']:
    st.title("🚨 ГО-Карта: Обучение по Приказу МЧС №429")
    st.markdown("""
    ### Добро пожаловать!

    Это **обучающее приложение** помогает понять, как распознавать **источники ЧС** и **действовать** в них,
    основываясь на **Приказе МЧС России №429**. Привязка к топооснове (карта Ижевска) — ключевая особенность.

    Нажимая кнопку "Принять условия", вы соглашаетесь с условиями использования приложения.
    """)
    if st.button("Прочитать условия"):
        st.session_state['show_terms'] = True
    if st.button("Принять условия"):
        st.session_state['accepted_terms'] = True
        st.rerun()
    if st.session_state.get('show_terms'):
        st.subheader("Условия использования:")
        st.markdown("""
        Правообладатель не несет ответственности за какие-либо прямые или косвенные последствия какого-либо использования или невозможности использования Приложения и/или ущерб, причиненный Пользователю и/или третьим сторонам в результате какого-либо использования, неиспользования или невозможности использования Приложения или отдельных его компонентов и/или функций, в том числе из-за возможных ошибок или сбоев в работе Приложения.

        Использование Приложения не требует регистрации или предоставления Пользователем своих персональных данных.

        С политикой конфиденциальности можно ознакомиться по ссылке: https://ссылка/
        """)
        if st.button("Принимаю"):
            st.session_state['accepted_terms'] = True
            st.session_state['show_terms'] = False
            st.rerun()
else:
    # --- Выбор района ---
    if not st.session_state['selected_district']:
        st.title("📍 Выберите район")
        st.markdown("""
        Пожалуйста, укажите район, где Вы находитесь, чтобы мы могли присылать Вам сообщения с экстренной информацией, актуальной для выбранного района.

        Мы можем определять регион автоматически и присылать сообщения с экстренной информацией в зависимости от того, где Вы находитесь в данный момент. Для этого необходимо активировать службу геолокации в настройках устройства и разрешить получать доступ к Вашему местоположению, в том числе, когда приложение не используется.

        Данные о местоположении используются для работы следующих функций:
        - получение сообщений с экстренной информацией по местоположению;
        - отправка сообщений, содержащих местоположение, в экстренные службы;
        - карта.
        """)
        districts = ["Ижевск", "Ленинский район", "Октябрьский район", "Первомайский район", "Устиновский район"]
        selected_district = st.selectbox("Выберите район", districts)
        if st.button("Продолжить"):
            st.session_state['selected_district'] = selected_district
            st.rerun()
    else:
        # --- Основная программа ---
        st.title("🚨 ГО-Карта: Обучение по Приказу МЧС №429")
        st.markdown(f"Вы выбрали район: **{st.session_state['selected_district']}**")

        # --- Навигация ---
        st.sidebar.header("Меню")
        menu = st.sidebar.radio(
            "",
            ["Главная", "Памятки", "Карта", "Добавить памятку", "Добавить здание"],
            key="navigation"
        )

        if menu == "Главная":
            # --- Геолокация ---
            st.subheader("📍 Ваше местоположение")

            # Геолокация (не поддерживается на Streamlit Cloud)
            st.info("📍 Геолокация недоступна. Пожалуйста, выберите адрес вручную или кликните на карте.")

            # Выбор по адресу
            address_input = st.text_input("Введите адрес (например, 'Ижевск, ул. Советская, 1')", value="")
            if st.button("Найти адрес"):
                if address_input.strip():
                    geolocator = Nominatim(user_agent="go_karta_training")
                    location = geolocator.geocode(address_input)
                    if location:
                        user_lat = location.latitude
                        user_lon = location.longitude
                        st.session_state['user_location'] = (user_lat, user_lon)
                        st.success(f"✅ Адрес найден: {location.address}. Координаты: {user_lat:.5f}, {user_lon:.5f}")
                    else:
                        st.error("❌ Адрес не найден. Попробуйте другой.")
                else:
                    st.warning("⚠️ Введите адрес.")

            # --- Выбор типа ЧС ---
            st.subheader("🔍 Выберите тип ЧС (обучение)")
            selected_emergency = st.selectbox(
                "Выберите ситуацию из Приказа МЧС №429",
                options=rules_df['type_ru'].tolist(),
                index=0,
                key="emergency_select_main"
            )
            if selected_emergency:
                st.session_state['selected_emergency'] = selected_emergency

            # --- Карта ---
            st.subheader("🗺️ Карта Ижевска и здания")

            # Центр карты
            center_lat = st.session_state['user_location'][0] if st.session_state['user_location'] else 56.8519
            center_lon = st.session_state['user_location'][1] if st.session_state['user_location'] else 53.2013

            # Создаём карту
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=13,
                tiles="OpenStreetMap"
            )

            # Добавляем здания из session_state
            for _, row in st.session_state['buildings_df'].iterrows():
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=f"""
                    <b>ID:</b> {row['id']}<br>
                    <b>Назначение:</b> {row['purpose']}<br>
                    <b>Этажность:</b> {row['floors']}<br>
                    <b>Материал:</b> {row['material']}
                    """,
                    icon=folium.Icon(color="blue", icon="home", prefix="fa")
                ).add_to(m)

            # Добавляем пользователя (если координаты введены)
            if st.session_state['user_location']:
                folium.Marker(
                    location=st.session_state['user_location'],
                    popup="📍 Вы здесь",
                    icon=folium.Icon(color="red", icon="user", prefix="fa")
                ).add_to(m)

            # Отображаем карту с возможностью клика
            map_data = st_folium(m, width="100%", height=500, key="main_map")

            # Обработка клика по карте
            if map_data and map_data.get('last_clicked'):
                clicked_lat = map_data['last_clicked']['lat']
                clicked_lon = map_data['last_clicked']['lng']
                st.session_state['user_location'] = (clicked_lat, clicked_lon)
                st.success(f"📍 Местоположение установлено кликом: Широта {clicked_lat:.5f}, Долгота {clicked_lon:.5f}")

            # --- Поиск ближайшего здания ---
            st.subheader("🏠 Ближайшее здание")
            if st.session_state['user_location']:
                user_coords = st.session_state['user_location']
                closest_building = None
                min_distance = float('inf')

                for _, row in st.session_state['buildings_df'].iterrows():
                    building_coords = (row['latitude'], row['longitude'])
                    distance = geodesic(user_coords, building_coords).meters
                    if distance < min_distance:
                        min_distance = distance
                        closest_building = row

                if closest_building is not None:
                    st.session_state['closest_building'] = closest_building
                    st.info(f"✅ Ближайшее здание: {closest_building['purpose']}, {closest_building['floors']} эт., {closest_building['material']}. Расстояние: {min_distance:.2f} м.")
                    st.markdown(f"**Рекомендация для здания:**")
                    if 'дерево' in closest_building['material'].lower():
                        st.warning("Деревянное здание — высок риск пожара. Эвакуируйтесь немедленно.")
                    elif 'кирпич' in closest_building['material'].lower() or 'бетон' in closest_building['material'].lower():
                        st.info("Кирпич/бетон — более устойчиво. Может служить укрытием, если нет других угроз.")
                    else:
                        st.info("Следуйте плану эвакуации для типа здания.")
                else:
                    st.warning("❌ Не удалось найти ближайшее здание.")
                    st.session_state['closest_building'] = None
            else:
                st.info("ℹ️ Укажите своё местоположение (по адресу или кликом на карте), чтобы найти ближайшее здание.")
                st.session_state['closest_building'] = None

            # --- План эвакуации или маршрут ---
            if st.session_state['user_location']:
                # Проверяем, есть ли ближайшее здание и находится ли пользователь "внутри" (расстояние < 5 метров)
                if st.session_state['closest_building'] is not None and min_distance < 5:
                    st.subheader("📋 План эвакуации")
                    building_plan_link = st.session_state['closest_building'].get('plan_link')
                    if building_plan_link:
                        st.markdown(f"План эвакуации для **{st.session_state['closest_building']['purpose']}** (ID: {st.session_state['closest_building']['id']}):")
                        st.image(building_plan_link, caption=f"План эвакуации для {st.session_state['closest_building']['purpose']}", use_container_width=True)
                    else:
                        st.info("План эвакуации для этого здания отсутствует.")
                else:
                    st.subheader("🏃‍♂️ Схема маршрута")
                    st.info("Схема маршрута от текущего местоположения до безопасной зоны будет отображена здесь. (Функция в разработке)")

            # --- Общие рекомендации ---
            st.subheader("📋 Общие рекомендации по типу ЧС")
            if st.session_state['selected_emergency']:
                rule_row = rules_df[rules_df['type_ru'] == st.session_state['selected_emergency']].iloc[0]
                st.markdown(f"**Тип ЧС:** {st.session_state['selected_emergency']}")
                st.markdown(f"**Действия:** {rule_row['actions_ru']}")
                st.info("✅ Следуйте этим шагам при возникновении подобной ЧС.")

            # --- Сценарий эвакуации ---
            st.subheader("🏃‍♂️ Сценарий эвакуации")
            if st.session_state['selected_emergency'] and st.session_state['user_location']:
                st.markdown(f"**Сценарий:** Представьте, что вы в Ижевске, рядом с вами произошла **{st.session_state['selected_emergency']}**.")
                st.markdown("1. 📍 Определите своё местоположение на карте.")
                st.markdown("2. 🏠 Найдите ближайшее укрытие или эвакуационный маршрут (отмечен на карте).")
                st.markdown("3. 🚨 Следуйте рекомендациям для выбранного типа ЧС.")
                st.markdown("4. ☎️ Сообщите о происшествии в МЧС: **112**.")
            else:
                st.info("ℹ️ Выберите тип ЧС и укажите своё местоположение для просмотра сценария.")

            # --- Подвал / укрытие ---
            st.subheader("🏗️ Где укрыться?")
            st.markdown("""
            - **Подвалы, цокольные этажи** капитальных зданий (бетон/кирпич).
            - **Укрытия** (указываются в планах, если есть).
            - **Дальше от окон**, вдали от возможных обломков.
            - **Не используйте лифты**.
            """)

            # --- Подвал / укрытие ---
            st.subheader("📚 Обучение")
            st.markdown("""
            **Приказ МЧС №429** определяет критерии ЧС по:
            - Типу (природные, техногенные, биологические и др.).
            - Масштабу (локальные, местные, региональные, федеральные).
            - Последствиям (жертвы, ущерб, нарушение жизнеобеспечения).

            Приложение упрощает их для **обывателя**.
            """)

        elif menu == "Памятки":
            st.subheader("📚 Памятки по действиям в ЧС")

            # --- Карточки с памятками в виде сетки 2x3 ---
            # Если нет памяток, создадим несколько фиктивных для демонстрации
            if not memos:
                # Фиктивные памятки (можно заменить на реальные)
                demo_memos = [
                    {
                        'title': 'Гражданская оборона',
                        'content': 'Основные принципы гражданской обороны.',
                        'image': 'https://via.placeholder.com/300x200/4a90e2/ffffff?text=Гражданская+оборона',
                        'video': None,
                        'category': 'Общее'
                    },
                    {
                        'title': 'Защита в чрезвычайных ситуациях',
                        'content': 'Как действовать при различных ЧС.',
                        'image': 'https://via.placeholder.com/300x200/f5a623/ffffff?text=Защита+в+ЧС',
                        'video': None,
                        'category': 'Общее'
                    },
                    {
                        'title': 'Пожарная безопасность',
                        'content': 'Правила поведения при пожаре.',
                        'image': 'https://via.placeholder.com/300x200/e74c3c/ffffff?text=Пожарная+безопасность',
                        'video': None,
                        'category': 'Пожар'
                    },
                    {
                        'title': 'Безопасность на водных объектах',
                        'content': 'Правила безопасности на водоемах.',
                        'image': 'https://via.placeholder.com/300x200/3498db/ffffff?text=Безопасность+на+воде',
                        'video': None,
                        'category': 'Вода'
                    },
                    {
                        'title': 'Первая помощь',
                        'content': 'Основы оказания первой помощи.',
                        'image': 'https://via.placeholder.com/300x200/2ecc71/ffffff?text=Первая+помощь',
                        'video': None,
                        'category': 'Медицина'
                    },
                    {
                        'title': 'Туристские группы',
                        'content': 'Безопасность в походах и туризме.',
                        'image': 'https://via.placeholder.com/300x200/9b59b6/ffffff?text=Туристские+группы',
                        'video': None,
                        'category': 'Туризм'
                    }
                ]
                memos = demo_memos

            # Разбиваем памятки на строки по 2 элемента
            for i in range(0, len(memos), 2):
                cols = st.columns(2)
                for j, memo in enumerate(memos[i:i+2]):
                    with cols[j]:
                        # Отображаем карточку
                        # Проверяем, есть ли изображение
                        if memo.get('image'):
                            try:
                                # Пытаемся отобразить изображение по пути
                                st.image(memo['image'], use_container_width=True)
                            except Exception as e:
                                # Если изображение не загрузилось, показываем плейсхолдер
                                st.warning("⚠️ Изображение недоступно")
                                st.image("https://via.placeholder.com/300x200/cccccc/000000?text=Изображение", use_container_width=True)
                        else:
                            # Если изображения нет, показываем плейсхолдер
                            st.image("https://via.placeholder.com/300x200/cccccc/000000?text=Без+изображения", use_container_width=True)

                        st.markdown(f"### {memo['title']}")
                        # Добавляем кнопки для действий
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Подробнее", key=f"memo_{i+j}_view"):
                                st.session_state['show_memo'] = memo['title']
                                st.rerun()
                        with col2:
                            if st.button("🗑️ Удалить", key=f"memo_{i+j}_delete"):
                                # Удаляем памятку из списка
                                memos.remove(memo)
                                # Сохраняем в файл
                                with open('memos.json', 'w', encoding='utf-8') as f:
                                    json.dump(memos, f, ensure_ascii=False, indent=4)
                                st.success(f"✅ Памятка '{memo['title']}' удалена!")
                                st.rerun()

            # --- Показ памятки ---
            if st.session_state['show_memo']:
                st.subheader(f"📖 Памятка: {st.session_state['show_memo']}")
                for memo in memos:
                    if memo['title'] == st.session_state['show_memo']:
                        st.markdown(memo['content'])
                        # Показ изображения, если оно есть и доступно
                        if memo.get('image'):
                            try:
                                st.image(memo['image'], caption="Изображение к памятке", use_container_width=True)
                            except Exception as e:
                                st.warning("⚠️ Изображение недоступно")
                                st.image("https://via.placeholder.com/600x400/cccccc/000000?text=Изображение+недоступно", caption="Изображение к памятке", use_container_width=True)

                        # Показ видео, если оно есть и доступно
                        if memo.get('video'):
                            try:
                                st.video(memo['video'])
                            except Exception as e:
                                st.warning("⚠️ Видео недоступно")
                                st.info("Видео не может быть воспроизведено. Убедитесь, что формат поддерживается (MP4, AVI, MOV).")
                        break
                if st.button("Назад"):
                    st.session_state['show_memo'] = None
                    st.rerun()

        elif menu == "Карта":
            st.subheader("🗺️ Карта Ижевска и здания")

            # Центр карты
            center_lat = 56.8519
            center_lon = 53.2013

            # Создаём карту
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=13,
                tiles="OpenStreetMap"
            )

            # Добавляем здания из session_state
            for _, row in st.session_state['buildings_df'].iterrows():
                folium.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=f"""
                    <b>ID:</b> {row['id']}<br>
                    <b>Назначение:</b> {row['purpose']}<br>
                    <b>Этажность:</b> {row['floors']}<br>
                    <b>Материал:</b> {row['material']}
                    """,
                    icon=folium.Icon(color="blue", icon="home", prefix="fa")
                ).add_to(m)

            # Отображаем карту
            st_folium(m, width="100%", height=500)

        elif menu == "Добавить памятку":
            st.subheader("➕ Добавить памятку")
            memo_title = st.text_input("Название памятки")
            memo_content = st.text_area("Текст памятки")
            memo_image = st.file_uploader("Загрузить изображение к памятке (необязательно)", type=["png", "jpg", "jpeg"])
            memo_video = st.file_uploader("Загрузить видео к памятке (необязательно)", type=["mp4", "avi", "mov"])

            if st.button("Сохранить памятку"):
                if memo_title and memo_content:
                    # Сохраняем изображение
                    image_path = None
                    if memo_image:
                        image_filename = f"{memo_title.replace(' ', '_')}_{memo_image.name}"
                        image_path = os.path.join("images", image_filename)
                        os.makedirs("images", exist_ok=True)
                        with open(image_path, "wb") as f:
                            f.write(memo_image.getbuffer())
                        st.success(f"✅ Изображение '{image_filename}' сохранено.")

                    # Сохраняем видео
                    video_path = None
                    if memo_video:
                        video_filename = f"{memo_title.replace(' ', '_')}_{memo_video.name}"
                        video_path = os.path.join("videos", video_filename)
                        os.makedirs("videos", exist_ok=True)
                        with open(video_path, "wb") as f:
                            f.write(memo_video.getbuffer())
                        st.success(f"✅ Видео '{video_filename}' сохранено.")

                    new_memo = {
                        'title': memo_title,
                        'content': memo_content,
                        'image': image_path,
                        'video': video_path
                    }
                    memos.append(new_memo)
                    # Сохраняем в файл
                    with open('memos.json', 'w', encoding='utf-8') as f:
                        json.dump(memos, f, ensure_ascii=False, indent=4)
                    st.success(f"✅ Памятка '{memo_title}' добавлена!")
                    st.rerun()
                else:
                    st.error("❌ Заполните все обязательные поля.")

        elif menu == "Добавить здание":
            st.subheader("➕ Добавить здание")
            building_id = st.number_input("ID здания", min_value=1)
            building_latitude = st.number_input("Широта", value=56.8519, format="%.5f")
            building_longitude = st.number_input("Долгота", value=53.2013, format="%.5f")
            building_floors = st.number_input("Этажность", min_value=1)
            building_material = st.text_input("Материал")
            building_purpose = st.text_input("Назначение")
            building_plan_link = st.text_input("Ссылка на план эвакуации (необязательно)")

            if st.button("Сохранить здание"):
                new_building = {
                    'id': int(building_id),
                    'latitude': building_latitude,
                    'longitude': building_longitude,
                    'floors': building_floors,
                    'material': building_material,
                    'purpose': building_purpose,
                    'plan_link': building_plan_link
                }
                # Добавляем новое здание в DataFrame в session_state
                new_row = pd.DataFrame([new_building])
                st.session_state['buildings_df'] = pd.concat([st.session_state['buildings_df'], new_row], ignore_index=True)
                st.success(f"✅ Здание '{building_purpose}' (ID: {building_id}) добавлено!")
                # st.rerun() # Не перезапускаем, так как данные в памяти

# --- Отладочный принт в конце ---
st.write("🚀 Все готово! Приложение работает.")
