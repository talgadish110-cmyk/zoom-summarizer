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
st.markdown('<div class="sub-header">מערכת מתקדמת עם מנגנון הגנה מעומסים להפקת סיכומי שיעור מלאים ומעמיקים!</div>', unsafe_allow_html=True)

# תפריט צד (Sidebar) להגדרות
with st.sidebar:
    st.header("⚙️ הגדרות מערכת")
    api_key_input = st.text_input("הכנס מפתח Google Gemini API Key", type="password", help="ניתן להשיג בחינם מ-Google AI Studio")
    
    # הגדרת מפתח ה-API כמשתנה סביבה
    if api_key_input:
        os.environ["GEMINI_API_KEY"] = api_key_input

    st.markdown("---")
    st.markdown("### 📋 רמת הפירוט המבוקשת")
    summary_depth = st.selectbox(
        "בחר עומק לסיכום",
        [
            "סיכום מורחב ומעמיק במיוחד (כולל פסקאות מלאות, הסברים טכניים ודוגמאות)",
            "סיכום כרונולוגי לפי סדר ההרצאה (מהדקה הראשונה ועד הסוף)",
            "סיכום טכני מלא + שאלות ותשובות שעלו מהקהל"
        ]
    )

# טאבים ראשיים
tab1, tab2, tab3 = st.tabs(["🚀 העלאת קובץ להפקה מורחבת", "🎙️ הקלטה חיה מהמיקרופון", "📖 הסבר והוראות"])

with tab1:
    st.markdown("### 📥 העלאת הקלטה קיימת")
    uploaded_file = st.file_uploader("בחר קובץ אודיו (MP3, WAV) או וידאו (MP4)", type=["mp4", "mov", "avi", "mkv", "webm", "mp3", "wav", "m4a"])
    
    if uploaded_file is not None:
        if st.button("התחל ניתוח עומק והפקת סיכום מורחב", type="primary", use_container_width=True):
            if not api_key_input:
                st.error("אנא הכנס מפתח API של Google Gemini בסיידבר הימני.")
            else:
                try:
                    client = genai.Client(api_key=api_key_input)
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        temp_path = tmp_file.name
                    
                    st.info("📤 מעלה את הקובץ לשרתי Google Gemini (עבור קובץ גדול זה ייקח מספר רגעים)...")
                    gemini_file = client.files.upload(file=temp_path)
                    st.success("הקובץ הועלה בהצלחה!")
                    
                    st.info("🧠 מנתח את ההקלטה בניתוח מעמיק ומפיק את הסיכום המורחב...")
                    
                    prompt = f"""
                    אתה מרצה מומחה, מתעד טכנולוגי וכותב תוכן מקצועי. הובאה בפניך הקלטת שיעור/פגישה מלאה.
                    מטרתך היא לכתוב **סיכום ארוך, מפורט מאוד, עשיר בתוכן ובבשר טכני**, ולא סיכום קצר או שטחי. 
                    
                    השתמש ברמת פירוט גבוהה מאוד (בסגנון של סיכום מחברת בחינה מלא של סטודנט מצטיין). הקפד לכלול:
                    
                    1. **מבוא והקשר מפורט:** רקע מלא על הנושאים שפותחו בתחילת השיעור, מטרת המפגש, והמונחים המרכזיים שהוצגו.
                    2. **גוף הסיכום (ניתוח מודולרי מלא):** פרק כל נושא שנדון בהרחבה. אל תסתפק בכותרות קצרות – כתוב פסקאות הסבר מלאות על כל מושג, תהליך, הגדרה ארכיטקטונית או דוגמה מעשית שהמרצה הציג. הוסף את כל ההקשרים והניואנסים שעלו.
                    3. **דיונים, שאלות ותשובות:** אם היו שאלות של משתתפים במהלך השיעור והתשובות עליהן, פרט אותן במלואן כחלק מההבנה הטכנית.
                    4. **כללים, הנחיות עבודה וזהב (Best Practices):** כל טיפ מעשי, אזהרה או כלל ברזל שהוזכר בשיעור (למשל בנוגע לאבטחה, תצורות או ניהול משאבים).
                    5. **משימות, תרגילים ומעבדות (Action Items):** רשימה מלאה של כל מה שהוגדר לביצוע עתידי, כולל דגשים לתרגילי בית.
                    
                    סגנון הכתיבה צריך להיות מקצועי, קריא מאוד, מחולק היטב לכותרות ותת-כותרות, פסקאות מפורטות, וטבלאות היכן שזה מוסיף ערך. אל תחסוך במילים ובמידע!
                    """
                    
                    # מנגנון חכם שמנסה שוב אוטומטית אם יש עומס (Rate Limit / 429)
                    max_retries = 3
                    retry_delay = 15
                    response = None
                    
                    for attempt in range(max_retries):
                        try:
                            response = client.models.generate_content(
                                model='gemini-3.6-flash',
                                contents=[gemini_file, prompt]
                            )
                            break
                        except Exception as api_err:
                            if "429" in str(api_err) and attempt < max_retries - 1:
                                st.warning(f"השרת עמוס (שגיאת מכסה 429). ממתין {retry_delay} שניות ומנסה שוב (ניסיון {attempt + 2} מתוך {max_retries})...")
                                time.sleep(retry_delay)
                                retry_delay += 10 # הגדלת זמן ההמתנה בהדרגה
                            else:
                                raise api_err
                    
                    if response:
                        st.success("הסיכום המורחב הופק בהצלחה!")
                        st.markdown("---")
                        st.markdown("### 📝 תוצאות הסיכום המעמיק")
                        st.markdown(response.text)
                        
                        st.download_button(
                            label="📥 הורד סיכום מורחב כמסמך טקסט",
                            data=response.text,
                            file_name="deep_detailed_summary.txt",
                            mime="text/plain"
                        )
                    
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                        
                except Exception as e:
                    st.error(f"אירעה שגיאה בתהליך הניתוח: {e}")

with tab2:
    st.markdown("### 🎙️ הקלטה חיה מהמיקרופון")
    st.info("💡 הקלט הרצאה או שיחה ישירות מהמיקרופון וקבל סיכום מעמיק בהתאם.")
    
    audio_value = st.audio_input("הקלט שיעור חי")
    
    if audio_value is not None:
        st.audio(audio_value)
        if st.button("סכם את ההקלטה החיה בניתוח עומק", type="primary", use_container_width=True):
            if not api_key_input:
                st.error("אנא הכנס מפתח API של Google Gemini בסיידבר הימני.")
            else:
                try:
                    client = genai.Client(api_key=api_key_input)
                    
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                        tmp_file.write(audio_value.getvalue())
                        temp_audio_path = tmp_file.name
                    
                    st.info("📤 מעלה את ההקלטה החיה...")
                    gemini_audio_file = client.files.upload(file=temp_audio_path)
                    st.success("ההקלטה הועלתה בהצלחה!")
                    
                    st.info("🧠 מנתח את ההקלטה החיה לעומק...")
                    
                    prompt_audio = f"""
                    אתה מתעד טכנולוגי מקצועי. ניתנת לך הקלטת אודיו של שיעור. 
                    אנא הפק סיכום ארוך, מפורט, עשיר בתוכן ובמושגים טכניים, הכולל פסקאות הסבר מלאות, כללים מרכזיים ומשימות לביצוע. אל תצמצם בפרטים!
                    """
                    
                    response_audio = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=[gemini_audio_file, prompt_audio]
                    )
                    
                    st.success("הסיכום המורחב הושלם!")
                    st.markdown("---")
                    st.markdown("### 📝 תוצאות הסיכום החי")
                    st.markdown(response_audio.text)
                    
                    st.download_button(
                        label="📥 הורד סיכום חי מורחב",
                        data=response_audio.text,
                        file_name="live_deep_summary.txt",
                        mime="text/plain"
                    )
                    
                    if os.path.exists(temp_audio_path):
                        os.remove(temp_audio_path)
                        
                except Exception as e:
                    st.error(f"אירעה שגיאה: {e}")

with tab3:
    st.markdown("### 📖 מדריך למשתמש")
    st.markdown("1. הפק מפתח API חדש ב-Google AI Studio במידת הצורך.")
    st.markdown("2. המערכת כוללת כעת מנגנון אוטומטי הממתין ומנסה שוב במקרה של עומס זמני מול השרת.")
