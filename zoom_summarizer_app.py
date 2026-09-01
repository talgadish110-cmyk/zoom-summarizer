import os
import tempfile
from google import genai
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
    '<div class="sub-header">העלה הקלטה (MP4, MP3 ועוד) או הקלט בשידור חי מהמיקרופון, ותן לבינה המלאכותית לסכם עבורך את הכל!</div>',
    unsafe_allow_html=True,
)

# תפריט צד (Sidebar) להגדרות
with st.sidebar:
    st.header("⚙️ הגדרות מערכת")
    api_key_input = st.text_input(
        "הכנס מפתח Google Gemini API Key",
        type="password",
        help="ניתן להשיג בחינם מ-Google AI Studio",
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

# טאבים ראשיים: העלאת קובץ מול הקלטה חיה
tab1, tab2, tab3 = st.tabs(
    ["📁 העלאת קובץ (MP4/MP3)", "🎤 הקלטה חיה מהמיקרופון", "📖 הסבר והוראות הרצה"]
)

with tab1:
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("### 📥 העלאת קובץ מהמחשב")
        uploaded_file = st.file_uploader(
            "בחר קובץ וידאו או אודיו",
            type=["mp4", "mov", "avi", "mkv", "webm", "mp3", "wav", "m4a"],
        )

    with col2:
        st.markdown("### 🤖 עיבוד וסיכום (מקובץ)")

        if st.button("התחל ניתוח וסיכום פגישה", type="primary", key="btn_file"):
            if not api_key_input:
                st.error("אנא הכנס מפתח API של Google Gemini בסיידבר הימני.")
            elif uploaded_file is None:
                st.warning("אנא בחר או העלה קובץ וידאו או אודיו תחילה.")
            else:
                try:
                    client = genai.Client(api_key=api_key_input)
                    file_extension = uploaded_file.name.split(".")[-1]
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=f".{file_extension}"
                    ) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        temp_path = tmp_file.name

                    st.info("📤 מעלה את הקובץ לשרתי Google Gemini...")
                    gemini_file = client.files.upload(file=temp_path)
                    st.success("הקובץ הועלה בהצלחה!")

                    st.info("🧠 מנתח את ההקלטה...")

                    prompt = f"""
                    אתה עוזר אישי מקצועי וחכם. ניתנת לך הקלטת פגישה (וידאו או אודיו).
                    אנא צור עבורי סיכום לפי הפורמט הבא: {summary_type}.
                    אם נבחר סיכום מלא מהתחלה ועד הסוף, סקור את כל מהלך הפגישה בסדר כרונולוגי מפורט מהדקה הראשונה ועד הסוף, כולל כל השלבים, הדיונים וההחלטות בצורה מלאה ולא מקוצרת.
                    כתוב בצורה נקייה, מסודרת ומקצועית בעברית.
                    """

                    # שימוש במודל העדכני gemini-3.6-flash שגוגל דורשת
                    response = client.models.generate_content(
                        model="gemini-3.6-flash", contents=[gemini_file, prompt]
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

                    if os.path.exists(temp_path):
                        os.remove(temp_path)

                except Exception as e:
                    st.error(f"אירעה שגיאה בתהליך הניתוח: {e}")

with tab2:
    st.markdown("### 🎙️ הקלטה חיה מהמיקרופון")
    st.info(
        "לחץ על כפתור ההקלטה בדפדפן כדי להקליט שיחה או פגישה בזמן אמת."
    )

    audio_value = st.audio_input("הקלט קול מהמיקרופון")

    if audio_value is not None:
        st.audio(audio_value)

        if st.button(
            "נתח והפק סיכום להקלטה החיה", type="primary", key="btn_mic"
        ):
            if not api_key_input:
                st.error("אנא הכנס מפתח API של Google Gemini בסיידבר הימני.")
            else:
                try:
                    client = genai.Client(api_key=api_key_input)

                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".wav"
                    ) as tmp_file:
                        tmp_file.write(audio_value.getvalue())
                        temp_path = tmp_file.name

                    st.info("📤 מעלה את ההקלטה לשרתי Google Gemini...")
                    gemini_file = client.files.upload(file=temp_path)
                    st.success("ההקלטה הועלתה בהצלחה!")

                    st.info("🧠 מנתח את ההקלטה החיה...")

                    prompt = f"""
                    הקלטה זו בוצעה בשידור חי דרך מיקרופון. אנא צור עבורה סיכום מפורט ומקצועי בעברית בהתאם לבחירה: {summary_type}.
                    אם נבחר סיכום מלא מהתחלה ועד הסוף, הצג סקירה רציפה ומלאה של כל מה שנאמר מהמילה הראשונה ועד האחרונה.
                    """

                    response = client.models.generate_content(
                        model="gemini-3.6-flash", contents=[gemini_file, prompt]
                    )

                    st.success("הסיכום הושלם בהצלחה!")
                    st.markdown("---")
                    st.markdown("### 📝 תוצאות הסיכום")
                    st.markdown(response.text)

                    st.download_button(
                        label="📥 הורד סיכום כקובץ טקסט",
                        data=response.text,
                        file_name="live_recording_summary.txt",
                        mime="text/plain",
                    )

                    if os.path.exists(temp_path):
                        os.remove(temp_path)

                except Exception as e:
                    st.error(f"אירעה שגיאה בתהליך הניתוח: {e}")

with tab3:
    st.markdown("### 📖 מדריך הרצה מהיר")
    st.markdown("1. בחר קובץ (MP4, MP3 וכו') או עבור לטאב ההקלטה החיה.")
    st.markdown("2. הזן את מפתח ה-API שלך בסיידבר הימני.")
    st.markdown(
        "3. בחר את פורמט הסיכום הרצוי (כמו סיכום מלא מהתחלה ועד הסוף)."
    )
    st.markdown("4. לחץ על כפתור הניתוח והמתן לתוצאה.")
