import os
import streamlit as st
from google import genai
import tempfile
import time
from gtts import gTTS
import io

st.set_page_config(
    page_title="סיכום שיעורי זום והקראה עם Gemini",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 סיכום שיעורי זום והקלטות עם Gemini והקראה קולית")
st.write("העלה הקלטת זום או שיעור כבד, קבל סיכום אקדמי מלא מהתחלה ועד הסוף, ותוכל אפילו לשמוע אותו בהקראה קולית!")

# שדה להכנסת מפתח יחיד של גוגל מ-AI Studio
gemini_api_key = st.text_input(
    "הכנס מפתח Google API (מ-Google AI Studio):", 
    value="", 
    type="password",
    placeholder="AIzaSy..."
)

uploaded_file = st.file_uploader(
    "📁 בחר קובץ הקלטת זום או שיעור (אודיו / וידאו גדולים)", 
    type=["mp3", "wav", "m4a", "mp4", "mov", "webm"]
)

if uploaded_file is not None:
    file_size_mb = uploaded_file.size / (1024 * 1024)
    st.info(f"📁 הקובץ נטען בהצלחה: {uploaded_file.name} ({file_size_mb:.2f} MB)")

    if gemini_api_key:
        if st.button("🚀 צור סיכום מלא לכל השיעור (מהתחלה ועד הסוף)", type="primary"):
            try:
                # שמירת הקובץ זמנית במערכת
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name

                g_client = genai.Client(api_key=gemini_api_key)

                with st.spinner("⏳ מעלה את קובץ השיעור הענק לגוגל ומאזין לו מהתחלה ועד הסוף... (עשוי לקחת דקה-שתיים)"):
                    # העלאת הקובץ ישירות ל-Gemini API (מצוין לקבצים גדולים וכבדים)
                    audio_file = g_client.files.upload(file=tmp_path)
                    
                    # המתנה עד שהקובץ יהיה מוכן לעיבוד בשרתים של גוגל
                    while audio_file.state.name == "PROCESSING":
                        time.sleep(3)
                        audio_file = g_client.files.get(name=audio_file.name)

                    if audio_file.state.name == "FAILED":
                        raise Exception("עיבוד הקובץ נכשל בצד של גוגל.")

                    # הנחיה לסיכום מלא, מפורט ומקיף לכל אורך השיעור
                    prompt = """
                    אתה עוזר אקדמי ומקצועי בכיר. להלן הקלטה מלאה של שיעור/הרצאה שהועלתה אלייך (מהתחלה ועד הסוף). 
                    אנא האזן לקובץ כולו בצורה יסודית, וצור עבורי **סיכום מלא, רחב, מקיף ומעמיק מאוד** בעברית. 
                    
                    הסיכום צריך להקיף את כל חלקי השיעור ולכלול:
                    1. **סקירה כללית ומבוא:** הנושאים המרכזיים שעלו לאורך כל השיעור.
                    2. **פירוט מלא של תוכן השיעור לפי סדר הדברים:** הסברים מפורטים, מושגים מקצועיים שהוסברו, רעיונות מרכזיים ודוגמאות שהובאו על ידי המרצה מההתחלה ועד הסיום.
                    3. **תובנות, מסקנות וסיכומים ביניים:** הדגשים החשובים ביותר שעלו מהדיון.
                    4. **משימות המשך או סיכומי Action Items:** מטלות, תרגולים או נושאים להמשך למידה אם הוזכרו בשיעור.
                    """

                    # שליחה למודל של גוגל
                    response = g_client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[audio_file, prompt]
                    )
                    
                    summary = response.text

                # ניקוי הקובץ הזמני מהדיסק
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

                # שמירת הסיכום בזיכרון של הסטרימלייט כדי שיישאר גם אחרי הקראה
                st.session_state['generated_summary'] = summary

            except Exception as e:
                st.error(f"שגיאה בתהליך: {e}")
    else:
        st.warning("⚠️ נא להזין את מפתח ה-Google API בשדה למעלה כדי להתחיל.")

# הצגת הסיכום אם קיים בזיכרון
if 'generated_summary' in st.session_state:
    summary = st.session_state['generated_summary']
    
    st.success("✅ הסיכום המלא הושלם בהצלחה!")
    st.markdown("---")
    st.markdown("### 📋 סיכום השיעור המלא מאת Gemini")
    st.markdown(summary)

    # כפתור הורדה כקובץ טקסט
    st.download_button(
        label="📥 הורד סיכום כקובץ טקסט",
        data=summary,
        file_name="Lesson_Full_Summary.txt",
        mime="text/plain"
    )

    # אפשרות הקראה קולית (Text-to-Speech)
    st.markdown("---")
    st.subheader("🎧 הקראה קולית של הסיכום")
    if st.button("🔊 הפק הקראה קולית לסיכום"):
        with st.spinner("מייצר קובץ שמע להקראה..."):
            try:
                # יצירת קובץ קולי בעברית מתוך טקסט הסיכום
                tts = gTTS(text=summary, lang='he', slow=False)
                tts_fp = io.BytesIO()
                tts.write_to_fp(tts_fp)
                tts_fp.seek(0)
                
                st.audio(tts_fp, format='audio/mp3')
                st.success("ההקראה מוכנה! תוכל להאזין לה ישירות כאן.")
            except Exception as tts_err:
                st.error(f"שגיאה ביצירת ההקראה הקולית: {tts_err}")
