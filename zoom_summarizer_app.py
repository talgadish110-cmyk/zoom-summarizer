import os
import time
import tempfile
import streamlit as st

st.set_page_config(page_title="Zoom Gemini Summarizer", page_icon="🎙️")
st.title("🎙️ Zoom Meeting Summarizer")

from google import genai

PROMPT = (
    "הקשב היטב להקלטת הפגישה המצורפת מהרגע הראשון ועד הסוף בלי לפספס דבר. "
    "הפק עבורי סיכום מקצועי, מקיף ומסודר הכולל: סקירה כללית, נקודות מרכזיות, "
    "והחלטות או פעולות המשך (Action Items)."
)

try:
    api_key = st.secrets["GEMINI_API_KEY"].strip()
except Exception:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()

uploaded = st.file_uploader("בחר קובץ אודיו", type=["mp3", "wav", "m4a"])

if uploaded and st.button("🚀 הפק סיכום"):
    if not api_key:
        st.error("חסר מפתח API")
        st.stop()

    tmp_path = None
    client = genai.Client(api_key=api_key)
    ref = None
    try:
        suffix = os.path.splitext(uploaded.name)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            f.write(uploaded.getbuffer())
            tmp_path = f.name

        with st.spinner("מעבד... אנא המתן"):
            ref = client.files.upload(file=tmp_path)
            while ref.state is not None and ref.state.name == "PROCESSING":
                time.sleep(3)
                ref = client.files.get(name=ref.name)
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[ref, PROMPT],
            )

        if resp.text:
            st.session_state["summary"] = resp.text
        else:
            st.warning("לא התקבל טקסט מג׳ימיני")
    except Exception as e:
        st.error("שגיאה:")
        st.exception(e)
    finally:
        if ref is not None:
            try:
                client.files.delete(name=ref.name)
            except Exception:
                pass
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

if "summary" in st.session_state:
    st.markdown("---")
    st.markdown(st.session_state["summary"])
    st.download_button(
        "📥 הורד כ־TXT",
        st.session_state["summary"],
        file_name="summary.txt",
        mime="text/plain",
    )
