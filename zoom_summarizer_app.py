import os
import time
import tempfile
from google import genai
from google.genai import errors
import streamlit as st

st.set_page_config(
    page_title="מערכת סיכום הקלטות זום חכמה",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Heebo', sans-serif;
        direction: rtl;
        text-align: right;
    }
    .stTextInput, .stFileUploader, .stButton {
        direction: rtl;
    }
    .main-header {
        font-size: 2.2rem;
        color: #1E3A8A;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #4B5563;
        margin-bottom: 2rem;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-header">🎥 מערכת חכמה לסיכום הקלטות זום (וידאו ואודיו)</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-header">העלה קובץ אודיו או בצע הקלטה חיה, ותן לבינה המלאכותית לסכם עבורך!</div>',
    unsafe_allow_html=True,
)

# שליפת המפתח מתוך ה-Secrets שהגדרת ב-Streamlit
api_key_input = st.secrets.get("GEMINI_API_KEY", "")

with st.sidebar:
    st.header("⚙️ הגדרות מערכת")
    if api_key_input:
        st.success("מפתח ה-API מוגדר בהצלחה במערכת.")
    else:
        st.error("חסר מפתח ב-Secrets.")

    st.markdown("---")
    st.markdown("### 📋 סוג הסיכום המבוקש")
    summary_type = st.selectbox(
        "בחר פורמט סיכום",
        [
            "סיכום מלא מהתחלה ועד הסוף (מפורט ורציף)",
            "סיכום מנהלים מקיף",
            "נקודות עיקריות ואקשן איטמס (Action Items)",
            "תמלול מלא עם תובנות",
            "סיכום לפי נושאים כרונולוגיים",
        ],
    )

tab1, tab2, tab3 = st.tabs(
    ["📁 העלאת קובץ (MP3/WAV)", "🎤 הקלטה חיה מהמיקרופון", "📖 הוראות"]
)

with tab1:
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("### 📥 העלאת קובץ מהמחשב")
        uploaded_file = st.file_uploader(
            "בחר קובץ אודיו (MP3 או WAV)",
            type=["mp3", "wav", "m4a"],
        )

    with col2:
        st.markdown("### 🤖 עיבוד וסיכום (מקובץ)")

        if st.button("התחל ניתוח וסיכום פגישה", type="primary", key="btn_file"):
            if not api_key_input:
                st.error("אנא הגדר את המפתח ב-Secrets.")
            elif uploaded_file is None:
                st.warning("אנא בחר או העלה קובץ אודיו תחילה.")
            else:
                try:
                    # טעינת המפתח בספרייה החדשה
                    os.environ["GEMINI_API_KEY"] = api_key_input
                    client = genai.Client()
                    
                    st.info("🔄 מעבד וקורא את הקובץ לזיכרון...")
                    file_bytes = uploaded_file.getvalue()
                    mime_type = uploaded_file.type if uploaded_file.type else "audio/mp3"

                    prompt = f"""
                    אתה עוזר אקדמי מקצועי. ניתנת לך הקלטת שיעור / פגישה.
                    אנא צור עבורי סיכום מפורט, מסודר ומעמיק לפי הפורמט הבא: {summary_type}.
                    
                    הנחיות:
                    1. סקור את עיקרי הדברים בצורה רציפה וכרונולוגית מרכזית.
                    2. כלול את המושגים המרכזיים, ההסברים וההחלטות שעלו בשיעור.
                    3. שמור על מבנה נקי, מקצועי וברור בעברית.
                    """

                    st.info("🧠 שולח לניתוח ב-Gemini...")

                    # שימוש במודל הפלאש היציב
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=[
                            {
                                "inline_data": {
                                    "data": file_bytes,
                                    "mime_type": mime_type
                                }
                            },
                            prompt
                        ],
                    )

                    st.success("הניתוח והסיכום הושלמו בהצלחה!")
                    st.markdown("---")
                    st.markdown("### 📝 תוצאות הסיכום")
                    st.markdown(response.text)

                    st.download_button(
                        label="📥 הורד סיכום כקובץ טקסט",
                        data=response.text,
                        file_name="meeting_summary.txt",
                        mime="text/plain",
                    )

                except Exception as e:
                    st.error(f"אירעה שגיאה בתהליך הניתוח: {e}")

with tab2:
    st.markdown("### 🎙️ הקלטה חיה מהמיקרופון")
    audio_value = st.audio_input("הקלט קול מהמיקרופון")

    if audio_value is not None:
        st.audio(audio_value)
        if st.button("נתח והפק סיכום להקלטה החיה", type="primary", key="btn_mic"):
            if not api_key_input:
                st.error("אנא הגדר מפתח ב-Secrets.")
            else:
                try:
                    os.environ["GEMINI_API_KEY"] = api_key_input
                    client = genai.Client()
                    audio_bytes = audio_value.getvalue()

                    st.info("🧠 מנתח את ההקלטה החיה...")
                    prompt = f"צור סיכום מפורט ומקצועי בעברית להקלטה זו לפי: {summary_type}"
                    
                    response = client.models.generate_content(
                        model="gemini-2.5-flash", 
                        contents=[
                            {
                                "inline_data": {
                                    "data": audio_bytes,
                                    "mime_type": "audio/wav"
                                }
                            },
                            prompt
                        ]
                    )

                    st.success("הסיכום הושלם בהצלחה!")
                    st.markdown("### 📝 תוצאות הסיכום")
                    st.markdown(response.text)

                except Exception as e:
                    st.error(f"אירעה שגיאה: {e}")

with tab3:
    st.markdown("### 📖 מדריך הרצה מהיר")
    st.markdown("1. המפתח מוגדר בבטחה ב-Secrets של האפליקציה.")
    st.markdown("2. העלה קובץ MP3 ולץ על כפתור הניתוח.")
