import os
import streamlit as st
import tempfile
import gdown
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
st.markdown('<div class="sub-header">העלה הקלטת זום או הדבק קישור מ-Google Drive, ותן לבינה המלאכותית לסכם עבורך את כל מה שנאמר והוצג במסך!</div>', unsafe_allow_html=True)

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
    st.info("💡 **טיפ:** מודל Gemini 1.5 Pro תומך בקבצי וידאו ואודיו ארוכים במיוחד (עד שעתיים ויותר) באופן ישיר!")

# טאבים ראשיים באפליקציה
tab1, tab2 = st.tabs(["🚀 העלאה וניתוח", "📖 הסבר והוראות הרצה"])

with tab1:
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.markdown("### 📥 מקור הקובץ")
        input_method = st.radio("בחר כיצד להזין את ההקלטה:", ["העלאת קובץ ישירות מהמחשב / נייד", "קישור מ-Google Drive (תמיכה בקבצים גדולים)"])
        
        video_file_path = None
        temp_dir = tempfile.mkdtemp()
        
        if input_method == "העלאת קובץ ישירות מהמחשב / נייד":
            uploaded_file = st.file_uploader("בחר קובץ וידאו (MP4, AVI, MOV) עד 2GB", type=["mp4", "mov", "avi", "mkv", "webm"])
            if uploaded_file is not None:
                video_file_path = os.path.join(temp_dir, uploaded_file.name)
                with open(video_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success("הקובץ הועלה בהצלחה!", icon="✅")
                st.video(video_file_path)
                
        else:
            drive_url = st.text_input("הדבק כאן קישור שיתוף ציבורי מ-Google Drive")
            if drive_url:
                if st.button("הורד קובץ מ-Google Drive"):
                    with st.spinner("מוריד את הקובץ מ-Google Drive (עשוי לקחת מספר דקות לקבצים גדולים)... אנא המתן"):
                        try:
                            # חילוץ מזהה הקובץ מהקישור בצורה חכמה
                            if "/d/" in drive_url:
                                file_id = drive_url.split('/d/')[1].split('/')[0]
                            elif "id=" in drive_url:
                                file_id = drive_url.split('id=')[1].split('&')[0]
                            else:
                                raise ValueError("פורמט קישור לא תקין")
                                
                            video_file_path = os.path.join(temp_dir, "zoom_recording.mp4")
                            
                            # שימוש בפרמטרים עוקפי אזהרות גוגל לקבצים גדולים
                            url = f'https://drive.google.com/uc?id={file_id}&export=download'
                            gdown.download(url, video_file_path, quiet=False, fuzzy=True)
                            
                            if os.path.exists(video_file_path) and os.path.getsize(video_file_path) > 1000:
                                st.success("הקובץ הורד בהצלחה!", icon="✅")
                                st.video(video_file_path)
                            else:
                                raise Exception("הקובץ שהורד ריק או שאין הרשאות צפייה ציבוריות.")
                        except Exception as e:
                            st.error(f"שגיאה בהורדת הקובץ: {e}")
                            st.info("💡 טיפ: ודא שהקובץ בדרייב מוגדר כציבורי ('Anyone with the link can view') ושאין לו הגבלת הורדה חריגה.")

    with col2:
        st.markdown("### 🤖 עיבוד וסיכום באמצעות AI")
        
        if st.button("התחל ניתוח וסיכום פגישה", type="primary", use_container_width=True):
            if not api_key_input:
                st.error("אנא הכנס מפתח API של Google Gemini בסיידבר הימני.")
            elif not video_file_path or not os.path.exists(video_file_path):
                st.warning("אנא בחר או העලා קובץ וידאו תחילה.")
            else:
                try:
                    client = genai.Client(api_key=api_key_input)
                    
                    with st.status("מעבד את הקלטת הזום...", expanded=True) as status:
                        st.write("📤 מעלה את קובץ המדיה לשרתי Google Gemini (הליך זה עשוי לקחת מספר דקות בהתאם לגודל הקובץ)...")
                        
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
    st.markdown("1. ודא שקובץ הדרישות `requirements.txt` מכיל את הספריות הנדרשות.")
    st.markdown("2. האפליקציה תומכת כעת בהורדה חכמה של קבצים גדולים מ-Google Drive באמצעות פרמטרים עוקפי אזהרות.")
