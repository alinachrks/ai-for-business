import os
import base64
import asyncio
import traceback
from PIL import Image
import streamlit as st
from transformers import AutoTokenizer
from stability_sdk import client
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from google.protobuf.json_format import MessageToJson
from components.config_dialog import *
from components.utils import *
from streamlit_lottie import st_lottie
import json


def app():
# Set global variables
    page_element = """
    <style>
    [data-testid="stAppViewContainer"]{
        background-image: url("https://i.ibb.co.com/3yVykRQ/Minimal-Photography-1-fotor-20240315111216.png");
        background-size: cover;
    }
    [data-testid="stHeader"]{
        background-color: rgba(0,0,0,0);
    }
    [data-testid="stToolbar"]{
        right: 2rem;
        background-image: url("https://cdn.iconscout.com/icon/free/png-256/hamburger-menu-462145.png");
        background-size: cover;
    }
    </style>
    """
    st.markdown(page_element, unsafe_allow_html=True)


    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.environ["TOKENIZERS_PARALLELISM"] = "false"


    # Check environment variables

    errors = []
    for key in [
        "OPENAI_API_KEY", "OPENAI_API_BASE", "OPENAI_API_TYPE", # For OpenAI APIs
        "STABILITY_HOST", "STABILITY_API_KEY",                  # For Stability APIs
    ]:
        if key not in os.environ:
            errors.append(f"Please set the {key} environment variable.")
    if len(errors) > 0:
        st.error("\n".join(errors))
        st.stop()

    stability_api = client.StabilityInference(
        key=os.environ['STABILITY_API_KEY'],  # API Key reference.
        # verbose=True,  # Print debug messages.
        engine="stable-diffusion-xl-1024-v1-0", # Set the engine to use for generation.
        # Available engines: stable-diffusion-xl-1024-v0-9 stable-diffusion-v1 stable-diffusion-v1-5 stable-diffusion-512-v2-0 stable-diffusion-768-v2-0
        # stable-diffusion-512-v2-1 stable-diffusion-768-v2-1 stable-diffusion-xl-beta-v2-2-2 stable-inpainting-v1-0 stable-inpainting-512-v2-0
    )

    ### FUNCTION DEFINITIONS ###


    @st.cache_data(show_spinner=False)
    def get_local_img(file_path: str) -> str:
        # Load a byte image and return its base64 encoded string
        return base64.b64encode(open(file_path, "rb").read()).decode("utf-8")


    @st.cache_data(show_spinner=False)
    def get_favicon(file_path: str):
        # Load a byte image and return its favicon
        return Image.open(file_path)


    @st.cache_data(show_spinner=False)
    def get_tokenizer():
        return AutoTokenizer.from_pretrained("gpt2", low_cpu_mem_usage=True)


    @st.cache_data(show_spinner=False)
    def get_css() -> str:
        # Read CSS code from style.css file
        with open(os.path.join(ROOT_DIR, "src", "style.css"), "r") as f:
            return f"<style>{f.read()}</style>"


    def get_chat_message(
        contents: str = "",
        align: str = "left"
    ) -> str:
        # Formats the message in an chat fashion (user right, reply left)
        div_class = "AI-line"
        color = "rgb(236, 235, 229)"
        file_path = os.path.join(ROOT_DIR, "src", "assets", "AI_icon.png")
        src = f"data:image/gif;base64,{get_local_img(file_path)}"
        if align == "right":
            div_class = "human-line"
            color = "rgb(177, 206, 224)"
            if "USER" in st.session_state:
                src = st.session_state.USER.avatar_url
            else:
                file_path = os.path.join(ROOT_DIR, "src", "assets", "user_icon.png")
                src = f"data:image/gif;base64,{get_local_img(file_path)}"
        icon_code = f"<img class='chat-icon' src='{src}' width=128 height=128 alt='avatar'>"
        formatted_contents = f"""
        <div class="{div_class}">
            {icon_code}
            <div class="chat-bubble" style="background: {color};">
            &#8203;{contents}
            </div>
        </div>
        """
        return formatted_contents

    async def main(human_prompt: str, selected_character: str = "Default") -> dict:
        res = {'status': 0, 'message': "Success"}
        try:
            # Update both chat log and the model memory
            st.session_state.LOG.append(f"Human: {human_prompt}")
            st.session_state.MEMORY.append({'role': "user", 'content': human_prompt})

            # Clear the input box after human_prompt is used
            prompt_box.empty()

            with chat_box:
                # Write the latest human message first
                line = st.session_state.LOG[-1]
                contents = line.split("Human: ")[1]
                st.markdown(get_chat_message(contents, align="right"), unsafe_allow_html=True)

                reply_box = st.empty()
                reply_box.markdown(get_chat_message(), unsafe_allow_html=True)

                # Step 1: Generate the AI-aided response using ChatGPT API
                response = await get_chatbot_reply_async(st.session_state.MEMORY)

                st.session_state.LOG.append(f"AI: {response}")
                st.session_state.MEMORY.append({'role': "assistant", 'content': response})

        except:
            res['status'] = 2
            res['message'] = traceback.format_exc()

        return res


    # Initialize some useful class instances
    with st.spinner("Initializing App..."):
        TOKENIZER = get_tokenizer()  # First time after deployment takes a few seconds


    ### MAIN STREAMLIT UI STARTS HERE ###


    # Define main layout
    st.title("Data Analytics and AI Application in Business")
    st.write("This chatbot serves as a virtual assistant, providing insights and guidance based on the latest advancements in AI and data analytics, empowering businesses to make informed decisions and stay competitive in their industries.")
    st.subheader("")
    

    # # Создаем кнопки с персонажами
    if 'selected_character' not in st.session_state:
        st.session_state.selected_character = st.write("Выбери тему")

    # Создание 4 столбцов
    col1, col2, col3, col4 = st.columns(4)

    # Заполнение первого столбца пустым элементом
    with col1:
        if st.button('Бизнес', help="Диалог о бизнесе"):
            st.session_state.selected_character = "Бизнес"

    # Создание кнопок для персонажей в оставшихся столбцах
    with col2:
        if st.button('Город', help="Урбанистика"):
            st.session_state.selected_character = "Город"

    with col3:
        if st.button('Технологии', help="Диалог о технологиях"):
            st.session_state.selected_character = "Технологии"

    with col4:
        if st.button('Помощь', help="Помогает ответить на вопросы"):
            st.session_state.selected_character = "Помощь"




    chat_box = st.container()
    st.write("")
    prompt_box = st.empty()
    footer = st.container()

    with footer:
        st.markdown("""
        <div align=right><small>
        Page views: <img src="https://www.cutercounter.com/hits.php?id=hxpaapo&nd=5&style=1" border="0" alt="best free website hit counter"></a><br>  
        Unique visitors: <img src="https://www.cutercounter.com/hits.php?id=hxpaapq&nd=5&style=1" border="0" alt="hit counter"></a><br>  
        GitHub <a href="https://github.com/alinachrks/rudolf/tree/master"><img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/alinachrks/rudolf?style=social"></a>  
        </small></div>
                    
        """, unsafe_allow_html=True)

    # Load CSS code
    st.markdown(get_css(), unsafe_allow_html=True)


    # Обновляем выбранный персонаж в состоянии сеанса
    # st.session_state.selected_character = selected_character

    # Получаем начальное приветственное сообщение для выбранного персонажа
    initial_prompt = INITIAL_PROMPTS.get(st.session_state.selected_character, "Default initial prompt")

    # Initialize/maintain a chat log and chat memory in Streamlit's session state
    # Log is the actual line by line chat, while memory is limited by model's maximum token context length
    if "MEMORY" not in st.session_state:
        st.session_state.MEMORY = [{'role': "system", 'content': initial_prompt}]
        st.session_state.LOG = [initial_prompt]



    # Render chat history so far
    with chat_box:
        for line in st.session_state.LOG[1:]:
            # For AI response
            if line.startswith("AI: "):
                contents = line.split("AI: ")[1]
                st.markdown(get_chat_message(contents), unsafe_allow_html=True)

            # For human prompts
            if line.startswith("Human: "):
                contents = line.split("Human: ")[1]
                st.markdown(get_chat_message(contents, align="right"), unsafe_allow_html=True)


    # Define an input box for human prompts
    with prompt_box:
        human_prompt = st.text_input("Треба подумати:", value="", key=f"text_input_{len(st.session_state.LOG)}")


    # Gate the subsequent chatbot response to only when the user has entered a prompt
    if len(human_prompt) > 0:
        run_res = asyncio.run(main(human_prompt, st.session_state.selected_character))  # Передаем выбранного персонажа в функцию main
        # if run_res['status'] == 0 and not DEBUG:
        if run_res['status'] == 0:
            st.rerun()

        else:
            if run_res['status'] != 0:
                st.error(run_res['message'])
            with prompt_box:
                if st.button("Show text input field"):
                    st.rerun()

    with st.sidebar:
        with open("animation/bird.json", "r", errors='ignore') as f:
            data = json.load(f)
        st_lottie(data)
