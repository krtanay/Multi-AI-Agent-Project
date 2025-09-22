import streamlit as st
import requests

from app.config.settings import settings
from app.common.logger import get_logger
from app.common.custom_exception import CustomException

logger = get_logger(__name__)

# Inject advanced custom CSS
st.markdown("""
<style>
body, .reportview-container {
    background: linear-gradient(135deg, #f7f2fa 0%, #d1d9ff 100%);
}
.stTextArea textarea {
    font-size: 1.08em;
    background: #F4EFFC;
    color: #301934;
    border-radius: 8px;
}
[data-testid="stHeader"] {
    background: linear-gradient(90deg,#6E44FF,#B594F9);
}
.stButton > button {
    background: linear-gradient(90deg,#6E44FF,#B594F9);
    color: #fff;
    font-size: 1.15em;
    border-radius: 8px;
    font-weight: semi-bold;
    box-shadow: 0 2px 8px #ceceee;
    transition: background 350ms;
}
.stButton > button:hover {
    background: linear-gradient(90deg,#B594F9,#6E44FF);
}
.ai-bubble {
    background: #FFFFFFCC;
    border-radius: 15px;
    padding: 1.2em;
    margin: 1em 0;
    font-size: 1.08em;
    color: #2c2452;
    border-left: 5px solid #6E44FF;
    box-shadow: 0 1px 8px #d1d9ff;
}
.user-bubble {
    background: #D1D9FFCC;
    border-radius: 15px;
    padding: 1em;
    margin: .5em 0;
    color: #301934;
    border-left: 5px solid #B594F9;
    font-size: 1.08em;
}
.mode-switch {
    text-align: right;
}
.example-links {
    color: #6E44FF; 
    font-size: 0.96em;
    margin-bottom: 1em;
}
::-webkit-scrollbar {width: 10px;}
::-webkit-scrollbar-thumb {background: #b6a1ea;}
</style>
""", unsafe_allow_html=True)

# Page config
st.set_page_config(page_title="🤖 Multi AI Agent Chat", page_icon="🧑‍🚀", layout="wide")

# Sidebar: Agent settings
st.sidebar.header("🛠️ Agent Setup")
system_prompt = st.sidebar.text_area("Agent Persona/Instructions", value="", height=65)
selected_model = st.sidebar.selectbox("Model Type", settings.ALLOWED_MODEL_NAMES)
allow_web_search = st.sidebar.checkbox("Web Search Enabled", value=True)

st.sidebar.markdown("---")
st.sidebar.markdown("💡 Try different agent personas!")

# Interactive help panel
with st.expander("💬 What can you do here?", expanded=False):
    st.markdown(
        """
        - 🤖 Configure agent mood/personality.
        - 🛠️ Select advanced models.
        - 🌍 Enable web powered answers.
        - ⚡ Paste research queries, creative tasks, coding, and more!
        """)
    st.markdown(
        '<span class="example-links">Examples:<br>'
        'System prompt: "You are a witty science teacher."<br>'
        'Query: "Explain quantum entanglement in simple terms."<br>'
        'System prompt: "Behavioral economics expert."<br>'
        'Query: "What are the effects of loss aversion?"</span>',
        unsafe_allow_html=True)

# User Query Section
st.markdown("### 👤 Your Query")
user_query = st.text_area("Type your message ...", height=120)

API_URL = "http://127.0.0.1:9999/chat"

if st.button("🚀 Send Query", key="ask_agent", type="primary"):
    if user_query.strip():
        # show user's message as bubble
        st.markdown(
            f'<div class="user-bubble"><b>👤 You:</b><br>{user_query.replace("\n", "<br>")}</div>',
            unsafe_allow_html=True
        )
        payload = {
            "model_name": selected_model,
            "system_prompt": system_prompt,
            "messages": [user_query],
            "allow_search": allow_web_search
        }
        try:
            logger.info("Sending request ...")
            with st.spinner("🧠 Agent is thinking ..."):
                response = requests.post(API_URL, json=payload)
            if response.status_code == 200:
                agent_response = response.json().get("response", "")
                logger.info("Response received")

                # Agent reply in colored bubble
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(
                    f'<div class="ai-bubble"><b>🤖 AI Agent:</b><br>{agent_response.replace("\n", "<br>")}</div>',
                    unsafe_allow_html=True
                )
            else:
                logger.error("Backend error")
                st.error("❌ Error: Backend not responding. Please try again.")
        except Exception as e:
            logger.error("API communication error")
            st.error(str(CustomException("❌ Failed to communicate with backend")))
    else:
        st.warning("🔔 Please enter a query before sending!")

# Add interactive footer tip
st.markdown("""
<hr>
<center>
    📝 <b>Tip:</b> Combine creative system prompts and queries! 
    <span style="color:#6E44FF;">Try: "You are Rabindranath Tagore, reply poetically to analysis requests."</span>
</center>
""", unsafe_allow_html=True)
