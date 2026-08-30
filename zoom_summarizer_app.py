import os
import streamlit as st
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
    .stTextInput, .stButton {
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
st.markdown('<div class="sub-header">ניתוח וסיכום פגישות זום באמצעות מודל Gemini המתקדם.</div>', unsafe_allow_html=True)

# תפריט צד (Sidebar) להגדרות
with st.sidebar:
    st.header("⚙️ הגדרות מערכת")
    api_key_input = st.text_input("הכנס מפתח Google Gemini API Key", type="password")
    
    st.markdown("---")
    st.markdown("### 📋 סוג הסיכום המבוקש")
    summary_type = st.selectbox(
        "בחר פורמט סיכום",
        ["סיכום מנהלים מקיף", "נקודות עיקריות ואקשן איטמס (Action Items)", "תמלול מלא עם תובנות", "סיכום לפי נושאים כרונולוגיים"]
    )

st.markdown("### 📥 ניתוח הקלטה באמצעות קישור קובץ (מומלץ לקבצים גדולים)")
st.info("💡 מכיוון שקבצי ענק מפילים את הדפדפן בהעלאה ישירה, הזן כאן את נתיב הקובץ המקומי בשרת או העלה קובץ קטן/אודיו בלבד.")

file_uri_input = st.text_input("הכנס נתיב קובץ מקומי או מזהה קובץ שכבר הועלה (לדוגמה מהלוג הקודם):")

if st.button("התחל ניתוח וסיכום פגישה", type="primary", use_container_width=True):
    if not api_key_input:
        st.error("אנא הכנס מפתח API של Google Gemini בסיידבר הימני.")
    elif not file_uri_input:
        st.warning("אנא הזן מזהה או נתיב קובץ תקין.")
    else:
        try:
            client = genai.Client(api_key=api_key_input)
            
            st.info("🧠 מנתח את ההקלטה באמצעות המודל...")
            
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
            
            # ניגש ישירות לקובץ שכבר הועלה ושמור במערכת של גוגל לפי המזהה שלו
            target_file = client.files.get(name=file_uri_input)
            
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=[target_file, prompt]
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
            
        except Exception as e:
            st.error(f"אירעה שגיאה בתהליך הניתוח: {e}")
