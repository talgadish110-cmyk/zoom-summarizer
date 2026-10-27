import os
import tempfile
import streamlit as st

st.set_page_config(page_title="Zoom Summarizer", page_icon="🎙️", layout="centered")

st.title("🎙️ Zoom Meeting Summarizer")

# בדיקת טעינת ספריית גוגל
try:
    from google import genai
    LIB_LOADED = True
except Exception as import_err:
    LIB_LOADED = False
    st.error(f"שגיאה בטעינת ספריית google-genai: {import_err}")

# שליפת מפתח ה־API
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))

if not api_key:
    st.warning("⚠️ מפתח ה־API (GEMINI_API_KEY) אינו מוגדר ב־Streamlit Secrets!")
else:
    st.success("✅ מפתח ה־API מזוהה במערכת.")

uploaded_file = st.file_uploader("בחר קובץ אודיו (MP3, WAV, M4A)", type=["mp3", "wav", "m4a"])

if uploaded_file is not None and LIB_LOADED:
    file_size_mb = uploaded_file.size / (1024 * 1024)
    st.success(f"הקובץ '{uploaded_file.name}' הועלה בהצלחה (גודל: {file_size_mb:.2f} MB)")
    
    if st.button("🚀 הפק סיכום מלא מג׳ימיני"):
        if not api_key:
            st.error("לא ניתן להמשיך ללא מפתח API.")
        else:
            tmp_path = None
            try:
                with st.spinner("מעבד את הקובץ מקומית..."):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name

                with st.spinner("מעלה לג׳ימיני ומייצר סיכום מלא... אנא המתן."):
                    client = genai.Client(api_key=api_key)
                    
                    # העלאת הקובץ לענן
                    audio_file_ref = client.files.upload(file=tmp_path)
                    
                    # הפקת סיכום
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

                    try:
                        client.files.delete(name=audio_file_ref.name)
                    except:
                        pass

            except Exception as e:
                st.error(f"שגיאה בתהליך העיבוד: {e}")
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
