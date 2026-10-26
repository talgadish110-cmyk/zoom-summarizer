import os
import tempfile
import gc
import streamlit as st
import google.generativeai as genai

# הגדרת עמוד Streamlit
st.set_page_config(
    page_title="Zoom Gemini Full Summarizer", 
    page_icon="🎙️", 
    layout="centered"
)

st.title("🎙️ Zoom Meeting Summarizer with Gemini")
st.write("העלה את קובץ האודיו (עד 2GB), תן לג׳ימיני להקשיב ולקבל סיכום מלא מהתחלה ועד הסוף עם אפשרות הורדה.")

# קבלת מפתח ה-API מתוך ה-Secrets של Streamlit
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))

if api_key:
    genai.configure(api_key=api_key)

# העלאת קובץ (MP3 או קבצי אודיו/וידאו נתמכים)
uploaded_file = st.file_uploader(
    "בחר קובץ הקלטה (MP3, WAV, M4A, MP4)", 
    type=["mp3", "wav", "m4a", "mp4"]
)

def process_with_gemini(file_path):
    """מעלה את הקובץ ל-Gemini API ומפיק סיכום מלא מתחילת הפגישה ועד סופה"""
    if not api_key:
        raise ValueError("מפתח API של Gemini (GEMINI_API_KEY) לא הוגדר ב-Streamlit Secrets!")

    st.info("שלב 1/2: מעלה את קובץ האודיו לענן של Gemini...")
    
    # העלאת הקובץ דרך ה-File API של גוגל
    audio_file_ref = genai.upload_file(file_path)
    
    st.info("שלב 2/2: ג׳ימיני מקשיב להקלטה ומכין סיכום מלא מהתחלה ועד הסוף... (פעולה זו עשויה לקחת דקה-שתיים)")

    prompt = """
    הקשב היטב להקלטת הפגישה המצורפת מהרגע הראשון ועד הסוף בלי לפספס דבר. 
    הפק עבורי סיכום מקצועי, מקיף ומסודר הכולל:
    1. **סקירה כללית** של נושאי הפגישה.
    2. **נקודות מרכזיות ודיונים עיקריים** שהועלו לכל אורך ההקלטה.
    3. **החלטות ופעולות המשך (Action Items)** ברורות שנקבעו בסיום.
    כתוב את הסיכום בשפה נקייה, מקצועית ומסודרת.
    """

    # שימוש במודל gemini-1.5-flash (היציב והמהיר ביותר לעיבוד אודיו ארוך)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([audio_file_ref, prompt])

    # מחיקת הקובץ מהשרת של גוגל לאחר קבלת התוצאה לשמירה על פרטיות
    try:
        genai.delete_file(audio_file_ref.name)
    except Exception:
        pass

    return response.text

if uploaded_file is not None:
    file_size_mb = uploaded_file.size / (1024 * 1024)
    st.success(f"הקובץ '{uploaded_file.name}' הועלה בהצלחה (גודל: {file_size_mb:.2f} MB)")
    
    if st.button("🚀 שלח לג׳ימיני לקבלת סיכום מלא"):
        tmp_path = None
        try:
            # שמירה זמנית ובטוחה בדיסק בחלקים (מונע קריסת RAM)
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                chunk_size = 1024 * 1024  # 1MB
                while True:
                    chunk = uploaded_file.read(chunk_size)
                    if not chunk:
                        break
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name

            # עיבוד ההקלטה מול ג׳ימיני
            with st.spinner("ג׳ימיני מקשיב ומעבד את ההקלטה... אנא המתן באורך רוח."):
                summary_result = process_with_gemini(tmp_path)

            if summary_result:
                st.markdown("---")
                st.subheader("📋 סיכום הפגישה מאת Gemini")
                st.markdown(summary_result)

                # הוספת כפתור הורדה (Download Button) לקובץ טקסט
                st.download_button(
                    label="📥 הורד את הסיכום כקובץ טקסט (TXT)",
                    data=summary_result,
                    file_name="zoom_meeting_summary.txt",
                    mime="text/plain"
                )

        except Exception as e:
            st.error(f"אירעה שגיאה במהלך העיבוד מול Gemini: {e}")

        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
            gc.collect()
