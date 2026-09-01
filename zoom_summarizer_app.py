import os
import requests
import json
import base64
import streamlit as st
from streamlit_mic_recorder import mic_recorder

st.set_page_config(
    page_title="מערכת סיכום הקלטות זום ומיקרופון",
    page_icon="🎙️",
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
    '<div class="main-header">🎙️ מערכת חכמה לסיכום פגישות והקלטות</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-header">העלה קובץ זום או דבר ישירות למיקרופון – ותן ל-Gemini לסכם עבורך!</div>',
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

# חלוקה לשתי לשוניות: העלאת קובץ או הקלטה חיה
tab1, tab2, tab3 = st.tabs(["📁 העלאת קובץ (MP3/WAV)", "🎙️ הקלטה ישירה מהמיקרופון", "📖 הוראות"])

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
                    st.info("🔄 מעבד את הקובץ ושולח ישירות לשרת...")
                    file_bytes = uploaded_file.getvalue()
                    mime_type = uploaded_file.type if uploaded_file.type else "audio/mp3"
                    
                    base64_audio = base64.b64encode(file_bytes).decode("utf-8")
                    
                    prompt = f"""
                    אתה עוזר אקדמי מקצועי. ניתנת לך הקלטת שיעור / פגישה.
                    אנא צור עבורי סיכום מפורט, מסודר ומעמיק לפי הפורמט הבא: {summary_type}.
                    
                    הנחיות:
                    1. סקור את עיקרי הדברים בצורה רציפה וכרונולוגית מרכזית.
                    2. כלול את המושגים המרכזיים, ההסברים וההחלטות שעלו בשיעור.
                    3. שמור על מבנה נקי, מקצועי וברור בעברית.
                    """

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
                    response = requests.post(url, headers=headers, data=json.dumps(payload))

                    if response.status_code == 200:
                        summary_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
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
                    else:
                        st.error(f"שגיאת שרת ({response.status_code}): {response.text}")

                except Exception as e:
                    st.error(f"אירעה שגיאה בתהליך הניתוח: {e}")

with tab2:
    st.markdown("### 🎙️ הקלטה קולית חיה")
    st.markdown("לחץ על כפתור ההקלטה למטה, דבר אל המיקרופון, ולחץ עצירה בסיום:")

    # רכיב ההקלטה החיה
    audio_recorded = mic_recorder(
        start_prompt="🔴 התחל הקלטה",
        stop_prompt="⏹️ עצור הקלטה",
        just_once=False,
        key="mic_recorder"
    )

    if audio_recorded:
        st.audio(audio_recorded['bytes'], format='audio/wav')
        
        if st.button("נתח וסכם את ההקלטה הקולית", type="primary", key="btn_mic"):
            if not api_key:
                st.error("אנא הגדר מפתח ב-Secrets.")
            else:
                try:
                    st.info("🔄 מעבד את ההקלטה שלך ושולח ל-Gemini...")
                    mic_bytes = audio_recorded['bytes']
                    base64_mic = base64.b64encode(mic_bytes).decode("utf-8")

                    prompt = f"""
                    אתה עוזר אקדמי מקצועי. ניתנה לך הקלטה קולית קצרה.
                    אנא צור עבורי סיכום מסודר וממוקד לפי הפורמט הבא: {summary_type}.
                    """

                    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
                    payload = {
                        "contents": [
                            {
                                "parts": [
                                    {"text": prompt},
                                    {
                                        "inline_data": {
                                            "mime_type": "audio/wav",
                                            "data": base64_mic
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                    headers = {"Content-Type": "application/json"}
                    response = requests.post(url, headers=headers, data=json.dumps(payload))

                    if response.status_code == 200:
                        summary_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
                        st.success("ההקלטה סוכמה בהצלחה!")
                        st.markdown("---")
                        st.markdown("### 📝 תוצאות הסיכום מהמיקרופון")
                        st.markdown(summary_text)

                        st.download_button(
                            label="📥 הורד סיכום כקובץ טקסט",
                            data=summary_text,
                            file_name="mic_summary.txt",
                            mime="text/plain",
                            key="download_mic"
                        )
                    else:
                        st.error(f"שגיאת שרת ({response.status_code}): {response.text}")

                except Exception as e:
                    st.error(f"אירעה שגיאה בניתוח ההקלטה: {e}")

with tab3:
    st.markdown("### 📖 מדריך הרצה מהיר")
    st.markdown("1. המפתח שלך מוגדר ב-Secrets.")
    st.markdown("2. תוכל לבחור בין העלאת קובץ אודיו מוכן לבין הקלטה חיה דרך הלשונית השנייה.")
