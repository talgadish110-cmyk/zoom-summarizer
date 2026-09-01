import time
import tempfile
import google.generativeai as genai
import streamlit as st

# הגדרת עמוד
st.set_page_config(
    page_title="מערכת סיכום הקלטות זום חכמה",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# עיצוב מותאם ותמיכה ב-RTL (עברית)
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
    '<div class="sub-header">העלה הקלטה או אודיו, ותן לבינה המלאכותית לסכם עבורך את הכל!</div>',
    unsafe_allow_html=True,
)

# תפריט צד (Sidebar) להגדרות - מפתח קבוע מראש לנוחותך
with st.sidebar:
    st.header("⚙️ הגדרות מערכת")
    
    api_key_input = st.text_input(
        "הכנס מפתח Google Gemini API Key",
        value="AQ.Ab8RN6JOCknVIFli07JNT-uy1KU5enVYMoEVDdCPBQAURvn_Pw",
        type="password",
        help="המפתח שלך מוגדר כאן."
    )

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
    ["📁 העלאת קובץ (MP3/WAV)", "🎤 הקלטה חיה מהמיקרופון", "📖 הסבר והוראות"]
)

with tab1:
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("### 📥 העלאת קובץ מהמחשב")
        uploaded_file = st.file_uploader(
            "בחר קובץ אודיו (מומלץ MP3)",
            type=["mp3", "wav", "m4a"],
        )

    with col2:
        st.markdown("### 🤖 עיבוד וסיכום (מקובץ)")

        if st.button("התחל ניתוח וסיכום פגישה", type="primary", key="btn_file"):
            if not api_key_input:
                st.error("אנא הכנס מפתח API תקין.")
            elif uploaded_file is None:
                st.warning("אנא בחר או העלה קובץ אודיו תחילה.")
            else:
                try:
                    # הגדרת המפתח בספרייה הקלאסית והיציבה
                    genai.configure(api_key=api_key_input)
                    
                    st.info("📤 מעלה את הקובץ לגוגל...")
                    
                    # העלאת קובץ דרך Files API של הספרייה הקלאסית (תומך במפתח רגיל לחלוטין)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        temp_path = tmp_file.name

                    audio_file = genai.upload_file(temp_path)
                    st.success("הקובץ הועלה בהצלחה!")

                    st.info("🧠 שולח לניתוח ב-Gemini...")

                    prompt = f"""
                    אתה עוזר אקדמי מקצועי. ניתנת לך הקלטת שיעור / פגישה.
                    אנא צור עבורי סיכום מפורט, מסודר ומעמיק לפי הפורמט הבא: {summary_type}.
                    
                    הנחיות:
                    1. סקור את עיקרי הדברים בצורה רציפה וכרונולוגית מרכזית.
                    2. כלול את המושגים המרכזיים, ההסברים וההחלטות שעלו בשיעור.
                    3. שמור על מבנה נקי, מקצועי וברור בעברית.
                    """

                    # שימוש במודל היציב והמהיר
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    response = model.generate_content([audio_file, prompt])

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

                    # ניקוי קובץ זמני
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

                except Exception as e:
                    st.error(f"אירעה שגיאה בתהליך הניתוח: {e}")

with tab2:
    st.markdown("### 🎙️ הקלטה חיה מהמיקרופון")
    audio_value = st.audio_input("הקלט קול מהמיקרופון")

    if audio_value is not None:
        st.audio(audio_value)
        if st.button("נתח והפק סיכום להקלטה החיה", type="primary", key="btn_mic"):
            if not api_key_input:
                st.error("אנא הכנס מפתח API.")
            else:
                try:
                    genai.configure(api_key=api_key_input)
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                        tmp_file.write(audio_value.getvalue())
                        temp_path = tmp_file.name

                    audio_file = genai.upload_file(temp_path)
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    
                    prompt = f"צור סיכום מפורט ומקצועי בעברית להקלטה זו לפי: {summary_type}"
                    response = model.generate_content([audio_file, prompt])

                    st.success("הסיכום הושלם בהצלחה!")
                    st.markdown("### 📝 תוצאות הסיכום")
                    st.markdown(response.text)

                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except Exception as e:
                    st.error(f"אירעה שגיאה: {e}")

with tab3:
    st.markdown("### 📖 מדריך הרצה מהיר")
    st.markdown("1. המפתח שלך כבר מוזן אוטומטית.")
    st.markdown("2. העלה קובץ MP3 שהמרת.")
    st.markdown("3. לחץ על כפתור הניתוח.")
