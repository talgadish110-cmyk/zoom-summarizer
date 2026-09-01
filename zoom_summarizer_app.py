import os
import tempfile
from google import genai
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
    '<div class="sub-header">העלה קובץ אודיו, ותן לבינה המלאכותית לסכם עבורך את הכל!</div>',
    unsafe_allow_html=True,
)

api_key = st.secrets.get("GEMINI_API_KEY", "")

with st.sidebar:
    st.header("⚙️ הגדרות מערכת")
    if api_key:
        st.success("מפתח ה-API מוגדר במערכת.")
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

tab1, tab2 = st.tabs(["📁 העלאת קובץ (MP3/WAV)", "📖 הוראות"])

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
            if not api_key:
                st.error("אנא הגדר מפתח ב-Secrets.")
            elif uploaded_file is None:
                st.warning("אנא בחר או העלה קובץ אודיו תחילה.")
            else:
                try:
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

                    # שימוש במשתנה הסביבה יחד עם הלקוח בצורה עוקפת
                    os.environ["GEMINI_API_KEY"] = api_key
                    
                    # אם המפתח מתחיל ב-AQ, נשתמש בבקשת HTTP ישירה שעוקפת את בדיקת ה-SDK הרשמי
                    if api_key.startswith("AQ"):
                        import requests
                        import json
                        import base64
                        
                        base64_audio = base64.b64encode(file_bytes).decode("utf-8")
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
                        
                        payload = {
                            "contents": [
                                {
                                    "parts": [
                                        {"text": prompt},
                                        {
                                            "inline_data": {
                                                "mime_type": mime_type,
                                                "data": base64_audio
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                        headers = {"Content-Type": "application/json"}
                        res = requests.post(url, headers=headers, data=json.dumps(payload))
                        
                        if res.status_code == 200:
                            summary_text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                        else:
                            raise Exception(f"שגיאת שרת ({res.status_code}): {res.text}")
                    else:
                        client = genai.Client()
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
                        summary_text = response.text

                    st.success("הניתוח והסיכום הושלמו בהצלחה!")
                    st.markdown("---")
                    st.markdown("### 📝 תוצאות הסיכום")
                    st.markdown(summary_text)

                    st.download_button(
                        label="📥 הורד סיכום כקובץ טקסט",
                        data=summary_text,
                        file_name="meeting_summary.txt",
                        mime="text/plain",
                    )

                except Exception as e:
                    st.error(f"אירעה שגיאה בתהליך הניתוח: {e}")

with tab2:
    st.markdown("### 📖 מדריך הרצה מהיר")
    st.markdown("1. המפתח מוגדר ב-Secrets.")
    st.markdown("2. העלה קובץ אודיו ולץ על כפתור הניתוח.")
