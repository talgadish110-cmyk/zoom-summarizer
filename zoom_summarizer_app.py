from google import genai
import streamlit as st

# הגדרת דף ה-Streamlit
st.set_page_config(
    page_title="Zoom Meeting Summarizer", page_icon="🎙️", layout="wide"
)

st.title("🎙️ מערכת מתקדמת לסיכום פגישות זום והקלטות")
st.write(
    "העלה קובץ שמע של פגישה (MP3 / WAV) וקבל ניתוח מעמיק, סיכום מפורט ותובנות מפתח."
)

# שליפת מפתח ה-API מתוך Streamlit Secrets
api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    st.warning("נא להגדיר את מפתח ה-API ב-Streamlit Secrets.")
else:
    # אתחול הלקוח של Google GenAI
    client = genai.Client(api_key=api_key)

    # העלאת קובץ שמע
    audio_file = st.file_uploader(
        "בחר קובץ שמע של הפגישה", type=["mp3", "wav", "m4a", "ogg"]
    )

    if audio_file is not None:
        st.audio(audio_file)
        st.success("הקובץ הועלה בהצלחה!")

        if st.button("התחל ניתוח עמוק והפקת סיכום מורחב"):
            with st.spinner(
                "מעלה את הקובץ לשרתי Google Gemini (עבור קובץ גדול זה ייקח מספר רגעים)..."
            ):
                try:
                    # שמירת הקובץ זמנית כדי שנוכל להעלות אותו ל-Files API של גוגל
                    with open("temp_audio_file", "wb") as f:
                        f.write(audio_file.getbuffer())

                    # העלאת הקובץ באמצעות ה-Files API הרשמי של google-genai
                    uploaded_file_ref = client.files.upload(
                        file="temp_audio_file"
                    )

                    st.info(
                        "הקובץ הועלה לשרת בהצלחה. ממתין לניתוח והפקת הסיכום..."
                    )

                    # הפעלת מודל gemini-2.0-flash לניתוח קובץ השמע
                    response = client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=[
                            uploaded_file_ref,
                            "אנא האזן לקובץ השמע הזה, נתח אותו בניתוח מעמיק, והפק סיכום מפורט ומקצועי בעברית הכולל את עיקרי הדברים, החלטות שהתקבלו ומשימות להמשך.",
                        ],
                    )

                    st.success("הניתוח הסתיים בהצלחה!")
                    st.markdown("### 📋 סיכום הפגישה:")
                    st.markdown(response.text)

                except Exception as e:
                    st.error(f"אירעה שגיאה בתהליך הניתוח: {e}")
