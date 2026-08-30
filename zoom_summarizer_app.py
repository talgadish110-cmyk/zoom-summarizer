import os
import time
import streamlit as st
import tempfile
from google import genai

# הגדרת עמוד
st.set_page_config(
    page_title="מערכת סיכום הקלטות זום חכמה",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# עיצוב מותאם ותמיכה ב-RTL (עברית)
st.markdown("""
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
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">🎥 מערכת חכמה לסיכום הקלטות זום (וידאו ואודיו)</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">העלה הקלטת זום מהמחשב או מהנייד, ותן לבינה המלאכותית לסכם עבורך את כל מה שנאמר!</div>', unsafe_allow_html=True)

# תפריט צד (Sidebar) להגדרות
with st.sidebar:
    st.header("⚙️ הגדרות מערכת")
    api_key_input = st.text_input("הכנס מפתח Google Gemini API Key", type="password", help="ניתן להשיג בחינם מ-Google AI Studio")
    
    st.markdown("---")
    st.markdown("### 📋 סוג הסיכום המבוקש")
    summary_type = st.selectbox(
        "בחר פורמט סיכום",
        ["סיכום מנהלים מקיף", "נקודות עיקריות ואקשן איטמס (Action Items)", "תמלול מלא עם תובנות", "סיכום לפי נושאים כרונולוגיים"]
    )

# טאבים ראשיים
tab1, tab2 = st.tabs(["🚀 העלאה וניתוח", "📖 הסבר והוראות הרצה"])

with tab1:
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown("### 📥 העלאת הקלטה")
        st.info("💡 בחר קובץ מהמחשב (מומלץ קובץ MP3 שהמרת).")
        
        uploaded_file = st.file_uploader("בחר קובץ וידאו או אודיו", type=["mp4", "mov", "avi", "mkv", "webm", "mp3", "wav", "m4a"])
        
    with col2:
        st.markdown("### 🤖 עיבוד וסיכום באמצעות AI")
        
        if st.button("התחל ניתוח וסיכום פגישה", type="primary", use_container_width=True):
            if not api_key_input:
                st.error("אנא הכנס מפתח API של Google Gemini בסיידבר הימני.")
            elif uploaded_file is None:
                st.warning("אנא בחר או העלה קובץ וידאו או אודיו תחילה.")
            else:
                try:
                    client = genai.Client(api_key=api_key_input)
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        temp_path = tmp_file.name
                    
                    st.info("📤 מעלה את הקובץ לשרתי Google Gemini...")
                    gemini_file = client.files.upload(file=temp_path)
                    st.success("הקובץ הועלה בהצלחה!")
                    
                    st.info("🧠 מנתח את ההקלטה באמצעות המודל העדכני...")
                    
                    prompt = f"""
                    אתה עוזר אישי מקצועי וחכם. ניתנת לך הקלטת פגישת זום (וידאו ואודיו).
                    אנא צור עבורי סיכום מקיף ברור ומקצועי בעברית לפי הסגנון הבא: {summary_type}.
                    
                    הסיכום צריך לכלול:
                    1. **סקירה כללית של הפגישה** (נושא מרכזי, משתתפים ומטרת הפגישה).
                    2. **נקודות מרכזיות שנדונו** (מחולקות לנושאים).
                    3. **החלטות משמעותיות שהתקבלו**.
                    4. **משימות לביצוע (Action Items)** כולל לוחות זמנים ואחראים אם צוינו בשיחה או הוצגו על המסך.
                    5. **תובנות ויזואליות חשובות** (שקופיות, גרפים או נתונים מרכזיים שהוצגו במהלך הפגישה).
                    
                    כתוב בצורה נקייה, מסודרת, מקצועית, עם כותרות בולטות.
                    """
                    
                    # שימוש במודל היציב gemini-2.0-flash
                    response = client.models.generate_content(
                        model='gemini-2.0-flash',
                        contents=[gemini_file, prompt]
                    )
                    
                    st.success("הניתוח והסיכום הושלמו בהצלחה!")
                    st.markdown("---")
                    st.markdown("### 📝 תוצאות הסיכום")
                    st.markdown(response.text)
                    
                    st.download_button(
                        label="📥 הורד סיכום כקובץ טקסט",
                        data=response.text,
                        file_name="zoom_meeting_summary.txt",
                        mime="text/plain"
                    )
                    
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                        
                except Exception as e:
                    st.error(f"אירעה שגיאה בתהליך הניתוח: {e}")

with tab2:
    st.markdown("### 📖 מדריך הרצה מהיר")
    st.markdown("1. בחר קובץ מהמחשב בלחיצת כפתור פשוטה.")
    st.markdown("2. הזן את מפתח ה-API שלך בצד ימין.")
    st.markdown("3. לחץ על כפתור התחלת ניתוח והתן למערכת לסכם עבורך אוטומטית.")
