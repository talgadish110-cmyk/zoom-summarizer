import os
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
st.markdown('<div class="sub-header">העלה הקלטת זום מהמחשב או מהנייד, ותן לבינה המלאכותית לסכם עבורך את כל מה שנאמר והוצג במסך!</div>', unsafe_allow_html=True)

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
    
    st.markdown("---")
    st.info("💡 **טיפ:** מודל Gemini 1.5 Pro תומך בקבצי וידאו ואודיו ארוכים במיוחד באופן ישיר!")

# טאבים ראשיים באפליקציה
tab1, tab2 = st.tabs(["🚀 העלאה וניתוח", "📖 הסבר והוראות הרצה"])

with tab1:
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown("### 📥 העלאת הקלטה")
        st.info("💡 מומלץ להעלות קבצי MP4. עבור קבצים גדולים (עד 2GB), אנא המתן בסבלנות עד שההעלאה תושלם במלואה.")
        
        video_file_path = None
        temp_dir = tempfile.mkdtemp()
        
        uploaded_file = st.file_uploader("בחר קובץ וידאו (MP4, AVI, MOV) עד 2GB", type=["mp4", "mov", "avi", "mkv", "webm"])
        if uploaded_file is not None:
            video_file_path = os.path.join(temp_dir, uploaded_file.name)
            with open(video_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success("הקובץ נטען בהצלחה לזיכרון הזמני ומוכן לניתוח!", icon="✅")

    with col2:
        st.markdown("### 🤖 עיבוד וסיכום באמצעות AI")
        
        if st.button("התחל ניתוח וסיכום פגישה", type="primary", use_container_width=True):
            if not api_key_input:
                st.error("אנא הכנס מפתח API של Google Gemini בסיידבר הימני.")
            elif not video_file_path or not os.path.exists(video_file_path):
                st.warning("אנא בחר או העלה קובץ וידאו תחילה.")
            else:
                try:
                    client = genai.Client(api_key=api_key_input)
                    
                    with st.status("מעבד את הקלטת הזום...", expanded=True) as status:
                        st.write("📤 מעלה את קובץ המדיה לשרתי Google Gemini (קבצים גדולים עשויים לקחת מספר דקות)...")
                        
                        gemini_file = client.files.upload(file=video_file_path)
                        st.write(f"✅ הקובץ הועלה בהצלחה (מזהה: {gemini_file.name})")
                        
                        st.write("🧠 מנתח את האודיו והווידאו של ההקלטה באמצעות מודל מולטימודלי מתקדם...")
                        
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
                        
                        response = client.models.generate_content(
                            model='gemini-1.5-pro',
                            contents=[gemini_file, prompt]
                        )
                        
                        status.update(label="הניתוח והסיכום הושלמו בהצלחה!", state="complete", expanded=False)
                    
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

with tab2:
    st.markdown("### 📖 מדריך הרצה מהיר")
    st.markdown("1. בחר קובץ וידאו מהמחשב או מהנייד (תומך בקבצים גדולים).")
    st.markdown("2. הזן את מפתח ה-API שלך בצד ימין.")
    st.markdown("3. לחץ על כפתור התחלת ניתוח והתן לבינה המלאכותית לסכם עבורך את הפגישה.")
