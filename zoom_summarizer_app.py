import os
import tempfile
import gc
import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Zoom Gemini Summarizer", page_icon="🎙️", layout="centered")

st.title("🎙️ Zoom Meeting Summarizer")
st.write("העלה את קובץ האודיו וקבל סיכום מלא מאת Gemini.")

# שליפת המפתח בצורה בטוחה
api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY"))

if api_key:
    genai.configure(api_key=api_key)

uploaded_file = st.file_uploader("בחר קובץ MP3", type=["mp3", "wav", "m4a"])

if uploaded_file is not None:
    st.success(f"הקובץ '{uploaded_file.name}' הועלה בהצלחה!")
    
    if st.button("🚀 שלח לג׳ימיני לקבלת סיכום"):
        if not api_key:
            st.error("מפתח ה-API אינו מוגדר ב-Streamlit Secrets!")
        else:
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                    tmp_file.write(uploaded_file.read())
                    tmp_path = tmp_file.name

                with st.spinner("מעלה את הקובץ לג׳ימיני ומעבד סיכום..."):
                    audio_ref = genai.upload_file(tmp_path)
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    response = model.generate_content([
                        audio_ref, 
                        "הקשב להקלטה מהתחלה ועד הסוף והפק סיכום מקיף הכולל סקירה, נקודות מרכזיות ופעולות המשך (Action Items)."
                    ])
                    
                    st.markdown("---")
                    st.subheader("📋 תוצאות הסיכום")
                    st.markdown(response.text)

                    st.download_button(
                        label="📥 הורד את הסיכום כקובץ טקסט (TXT)",
                        data=response.text,
                        file_name="summary.txt",
                        mime="text/plain"
                    )

                    try:
                        genai.delete_file(audio_ref.name)
                    except:
                        pass

            except Exception as e:
                st.error(f"שגיאה בתהליך: {e}")
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except:
                        pass
                gc.collect()
