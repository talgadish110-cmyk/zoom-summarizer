import os
import tempfile
import gc
import streamlit as st

# הגדרת עמוד Streamlit
st.set_page_config(
    page_title="Zoom Gemini Summarizer", 
    page_icon="🎙️", 
    layout="centered"
)

st.title("🎙️ Zoom Meeting Summarizer")
st.write("העלה את קובץ האודיו (עד 2GB) וקבל סיכום מלא מאת Gemini.")

# שליפת מפתח ה־API בצורה בטוחה לחלוטין שלא תגרום לקריסת האפליקציה
api_key = None
try:
    api_key = st.secrets.get("GEMINI_API_KEY")
except Exception:
    pass

if not api_key:
    api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    st.warning("⚠️ מפתח ה־API (GEMINI_API_KEY) אינו מוגדר ב־Streamlit Secrets. אנא ודא שהגדרת אותו בהגדרות האפליקציה.")
else:
    st.success("✅ מפתח ה־API מוגדר וטעון בהצלחה!")

# העלאת קובץ אודיו
uploaded_file = st.file_uploader(
    "בחר קובץ הקלטה (MP3, WAV, M4A)", 
    type=["mp3", "wav", "m4a"]
)

if uploaded_file is not None:
    file_size_mb = uploaded_file.size / (1024 * 1024)
    st.success(f"הקובץ '{uploaded_file.name}' הועלה בהצלחה (גודל: {file_size_mb:.2f} MB)")
    
    if st.button("🚀 הפק סיכום מלא מג׳ימיני"):
        if not api_key:
            st.error("לא ניתן לשלוח לג׳ימיני כיוון שמפתח ה־API חסר.")
        else:
            tmp_path = None
            try:
                # שמירה זמנית ובטוחה בדיסק בחלקים
                with st.spinner("מעבד ושומר את הקובץ מקומית..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
                        chunk_size = 1024 * 1024
                        while True:
                            chunk = uploaded_file.read(chunk_size)
                            if not chunk:
                                break
                            tmp_file.write(chunk)
                        tmp_path = tmp_file.name

                with st.spinner("מעלה את הקובץ לענן של ג׳ימיני וממתין לסיכום... אנא המתן."):
                    from google import genai
                    client = genai.Client(api_key=api_key)
                    
                    # העלאת הקובץ דרך ה-File API
                    audio_file_ref = client.files.upload(file=tmp_path)
                    
                    # קבלת סיכום ממודל gemini-2.5-flash
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[
                            audio_file_ref, 
                            "הקשב היטב להקלטת הפגישה המצורפת מהרגע הראשון ועד הסוף בלי לפספס דבר. הפק עבורי סיכום מקצועי, מקיף ומסודר הכולל: סקירה כללית, נקודות מרכזיות, והחלטות או פעולות המשך (Action Items)."
                        ]
                    )
                    
                    st.markdown("---")
                    st.subheader("📋 תוצאות הסיכום המלא")
                    st.markdown(response.text)

                    # כפתור הורדה
                    st.download_button(
                        label="📥 הורד את הסיכום כקובץ TXT",
                        data=response.text,
                        file_name="zoom_meeting_summary.txt",
                        mime="text/plain"
                    )

                    # ניקוי הקובץ מהשרת של גוגל
                    try:
                        client.files.delete(name=audio_file_ref.name)
                    except:
                        pass

            except Exception as e:
                st.error(f"שגיאה בתהליך מול Gemini: {e}")
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
                gc.collect()
