import os
import time
import tempfile
import gc
import streamlit as st

st.set_page_config(page_title="Zoom Gemini Summarizer", page_icon="🎙️", layout="centered")

st.markdown(
    "<style>.stMarkdown, .stAlert {direction: rtl; text-align: right;}</style>",
    unsafe_allow_html=True,
)

st.title("🎙️ Zoom Meeting Summarizer")

try:
    from google import genai
except ImportError as e:
    st.error(f"שגיאה בטעינת הספרייה: {e}")
    st.stop()

api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))

PROMPT = (
    "הקשב היטב להקלטת הפגישה המצורפת מהרגע הראשון ועד הסוף בלי לפספס דבר. "
    "הפק עבורי סיכום מקצועי, מקיף ומסודר הכולל: סקירה כללית, נקודות מרכזיות, "
    "והחלטות או פעולות המשך (Action Items)."
)


def wait_until_active(client, file_ref, timeout=600, interval=3):
    """ממתין עד שהקובץ מעובד ומוכן לשימוש."""
    start = time.time()
    while file_ref.state.name == "PROCESSING":
        if time.time() - start > timeout:
            raise TimeoutError("עיבוד הקובץ ארך יותר מדי זמן")
        time.sleep(interval)
        file_ref = client.files.get(name=file_ref.name)
    if file_ref.state.name != "ACTIVE":
        raise RuntimeError(f"עיבוד הקובץ נכשל (מצב: {file_ref.state.name})")
    return file_ref


uploaded_file = st.file_uploader("בחר קובץ אודיו (MP3, WAV, M4A)", type=["mp3", "wav", "m4a"])

if uploaded_file is not None:
    file_size_mb = uploaded_file.size / (1024 * 1024)
    st.success(f"הקובץ '{uploaded_file.name}' הועלה בהצלחה (גודל: {file_size_mb:.2f} MB)")

    if st.button("🚀 הפק סיכום מלא מג׳ימיני"):
        if not api_key:
            st.error("מפתח ה־API (GEMINI_API_KEY) אינו מוגדר ב־Streamlit Secrets!")
        else:
            tmp_path = None
            client = None
            audio_file_ref = None
            try:
                suffix = os.path.splitext(uploaded_file.name)[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                    tmp_file.write(uploaded_file.getbuffer())
                    tmp_path = tmp_file.name

                with st.spinner("מעלה את הקובץ לג׳ימיני ומייצר סיכום מלא... אנא המתן."):
                    client = genai.Client(api_key=api_key)
                    audio_file_ref = client.files.upload(file=tmp_path)
                    audio_file_ref = wait_until_active(client, audio_file_ref)

                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[audio_file_ref, PROMPT],
                    )

                if response.text:
                    st.session_state["summary"] = response.text
                else:
                    st.warning("ג׳ימיני לא החזיר טקסט (ייתכן שהתשובה נחסמה).")

            except Exception as inner_e:
                st.error(f"שגיאה בתהליך מול Gemini: {inner_e}")
            finally:
                if client and audio_file_ref:
                    try:
                        client.files.delete(name=audio_file_ref.name)
                    except Exception:
                        pass
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
                gc.collect()

if "summary" in st.session_state:
    st.markdown("---")
    st.subheader("📋 תוצאות הסיכום המלא")
    st.markdown(st.session_state["summary"])

    st.download_button(
        label="📥 הורד את הסיכום כקובץ TXT",
        data=st.session_state["summary"],
        file_name="zoom_meeting_summary.txt",
        mime="text/plain",
    )
