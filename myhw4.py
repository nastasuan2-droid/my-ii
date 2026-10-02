import io
import urllib.parse
import cv2
import numpy as np
from PIL import Image
import requests
import streamlit as st


st.set_page_config(
    page_title="Smart Photo Editor & AI Generator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    .main {
        background-color: #0f172a;
        color: #f8fafc;
    }
    .title-text {
        font-size: 2.8rem !important;
        font-weight: 800;
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .subtitle-text {
        text-align: center;
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .stDownloadButton > button {
        width: 100%;
        background: linear-gradient(90deg, #2563eb, #7c3aed);
        color: white;
        border: none;
        padding: 0.6rem 1rem;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    .stDownloadButton > button:hover {
        background: linear-gradient(90deg, #1d4ed8, #6d28d9);
        box-shadow: 0 4px 12px rgba(124, 58, 237, 0.4);
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<p class="title-text">🎨 Smart Photo Editor & AI Generator</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="subtitle-text">Згенеруйте зображення за допомогою ШІ або завантажте власне, та застосуйте стильні фільтри!</p>',
    unsafe_allow_html=True,
)


def generate_image(prompt):
    try:
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed=42"
        response = requests.get(url, timeout=45)
        if response.status_code == 200:
            return response.content, None
        else:
            return None, f"Сервіс недоступний. ({response.status_code})"
    except Exception as e:
        return None, f"Помилка: {e}"


st.sidebar.markdown("## ⚙️ Налаштування")

source_type = st.sidebar.radio(
    "Оберіть джерело зображення:",
    ["🤖 ШІ Генерація", "📁 Завантажити з ПК"],
    key="source_type_select"
)

input_image = None

if source_type == "🤖 ШІ Генерація":
    st.sidebar.markdown("---")
    prompt = st.sidebar.text_area(
        "Опис для ШІ:",
        placeholder="Наприклад: Лисиця сидить у лісі біля дерева",
        key="ai_prompt"
    )

    STYLES = {
        "Без стилю": "",
        "Реалістичний": "high detail, photorealistic, natural lighting",
        "Акварель": "watercolor painting style, soft edges, pastel colors",
        "Мультяшний": "3D animated movie style, vibrant colors, friendly look",
        "Піксель-Арт": "pixel art style, 16-bit retro game aesthetic",
    }

    style_choice = st.sidebar.selectbox("Стиль генерації:", list(STYLES.keys()), key="ai_style")

    if st.sidebar.button("✨ Згенерувати зображення", key="gen_btn"):
        if prompt.strip():
            final_prompt = prompt + " " + STYLES[style_choice]
            with st.spinner("AI генерує зображення..."):
                image_bytes, error = generate_image(final_prompt)
                if error:
                    st.error(error)
                elif image_bytes:
                    st.session_state["raw_ai_bytes"] = image_bytes
        else:
            st.warning("Будь ласка, введіть опис зображення.")

    if "raw_ai_bytes" in st.session_state:
        input_image = Image.open(io.BytesIO(st.session_state["raw_ai_bytes"]))

else:
    st.sidebar.markdown("---")
    uploaded_file = st.sidebar.file_uploader(
        "Завантажте фото", type=["png", "jpg", "jpeg"], key="file_uploader"
    )
    if uploaded_file is not None:
        input_image = Image.open(uploaded_file)


if input_image is not None:
    img_array = np.array(input_image.convert("RGB"))

    st.sidebar.markdown("---")
    filter_option = st.sidebar.selectbox(
        "🔮 Оберіть ефект (фільтр):",
        [
            "Оригінал",
            "Чорно-біле",
            "Розмиття (Blur)",
            "Дзеркальне відображення",
            "Налаштування яскравості",
            "Налаштування контрасту",
            "Інверсія кольорів",
        ],
        key="filter_select"
    )

    processed_img = img_array.copy()

    if filter_option == "Чорно-біле":
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        processed_img = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

    elif filter_option == "Розмиття (Blur)":
        blur_val = st.sidebar.slider("Інтенсивність розмиття", 1, 31, 15, step=2, key="blur_slider")
        processed_img = cv2.GaussianBlur(img_array, (blur_val, blur_val), 0)

    elif filter_option == "Дзеркальне відображення":
        flip_type = st.sidebar.radio("Напрямок:", ["По горизонталі", "По вертикалі"], key="flip_radio")
        code = 1 if flip_type == "По горизонталі" else 0
        processed_img = cv2.flip(img_array, code)

    elif filter_option == "Налаштування яскравості":
        brightness_val = st.sidebar.slider("Рівень яскравості", -100, 100, 0, key="bright_slider")
        processed_img = cv2.convertScaleAbs(img_array, alpha=1.0, beta=brightness_val)

    elif filter_option == "Налаштування контрасту":
        contrast_val = st.sidebar.slider("Рівень контрасту", 0.5, 3.0, 1.0, step=0.1, key="contrast_slider")
        processed_img = cv2.convertScaleAbs(img_array, alpha=contrast_val, beta=0)

    elif filter_option == "Інверсія кольорів":
        processed_img = 255 - img_array

    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown("### 📷 Вхідне зображення")
        st.image(img_array, use_container_width=True)

    with col2:
        st.markdown("### ✨ Результат з фільтром")
        st.image(processed_img, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        result_image = Image.fromarray(processed_img)
        buf = io.BytesIO()
        result_image.save(buf, format="JPEG", quality=95)
        byte_im = buf.getvalue()

        st.download_button(
            label="📥 Завантажити оброблене фото",
            data=byte_im,
            file_name="edited_image.jpeg",
            mime="image/jpeg",
            key="download_btn"
        )
else:
    st.info("👈 Оберіть джерело в меню ліворуч: згенеруйте зображення через ШІ або завантажте власне фото!")