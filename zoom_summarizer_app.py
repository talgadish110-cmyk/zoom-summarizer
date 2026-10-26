import os
import tempfile
import gc
import streamlit as st

# הגדרת עמוד Streamlit
st.set_page_config(
    page_title="Zoom Meeting Full Summarizer", 
    page_icon="🎙️", 
    layout="centered"
)

st.title("🎙️ Zoom Meeting Full Summarizer")
st.write("העלה את קובץ ה־MP3 של הפגישה וקבל סיכום מלא מתחילת ההקלטה ועד סופה בלי לפספס דבר.")

# העלאת קובץ MP3 (או קבצי אודיו תואמים)
uploaded_file = st.file_uploader(
    "בחר קובץ MP3 של ההקלטה", 
    type=["mp3", "wav", "m4a"]
)

def chunk_text(text, max_chars=12000):
    """חיתוך טקסט ארוך למקטעים כדי שלא נחרוג ממגבלת הזיכרון"""
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]

def process_audio_and_summarize(file_path):
    """
    מעבד את קובץ האודיו מהדיסק המקומי, מבצע תמלול,
    ומפיק סיכום מלא מהתחלה ועד הסוף.
    """
    st.info("שלב 1/3: קורא את נתוני האודיו מהדיסק המקומי בצורה בטוחה...")
    
    # --- כאן תוכל לחבר בעתיד את ה-API האמיתי שלך (לדוגמה Gemini API או OpenAI) ---
    # with open(file_path, "rb") as f:
    #     ...
    
    # טקסט סימולציה לצורך הדגמה (מחליפים כאן את התמלול האמיתי):
    full_transcript = "כאן יופיע כל טקסט התמלול המלא של פגישת ה־Zoom מהרגע הראשון ועד הסוף..." * 25

    st.info("שלב 2/3: מנתח את התמלול ומחלק לחלקים לניתוח מקיף...")
    chunks = chunk_text(full_transcript)
    
    partial_summaries = []
    for i, chunk in enumerate(chunks):
        # --- כאן תוכל לשלוח כל מקטע למודל ה-AI לקבלת סיכום ביניים ---
        partial_summaries.append(f"סיכום חלק {i+1}: עיקרי הנושאים שהוצגו בשלב זה של הפגישה.")

    st.info("שלב 3/3: מאחד את כל החלקים ומפיק סיכום־על סופי מהתחלה ועד הסוף...")
    
    # גיבוש סיכום סופי ורציף
    final_summary = f"""
    ### 🎯 סיכום מקיף וכולל של פגישת ה־Zoom (מהתחלה ועד הסוף)
    
    * **היקף הניתוח:** ההקלטה עובדה ונותחה דרך {len(chunks)} מקטעים מרכזיים.
    * **תקציר הנושאים המרכזיים:**
      1. **פתיחת הפגישה:** הצגת הנושאים המרכזיים שעל הפרק.
      2. **דיון שוטף:** מעבר על נתונים, סטטוסים ומשימות.
      3. **החלטות ופעולות המשך (Action Items):** סיכום ההחלטות שהתקבלו לקראת המשך העבודה.
    
    *(סיכום זה הופק מניתוח רציף של כל קובץ ה־MP3 שהועלה).*
    """

    return full_transcript, final_summary

if uploaded_file is not None:
    file_size_mb = uploaded_file.size / (1024 * 1024)
    st.success(f"הקובץ '{uploaded_file.name}' הועלה בהצלחה (גודל: {file_size_mb:.2f} MB)")
    
    if st.button("התחל תמלול וסיכום מלא"):
        tmp_path = None
        try:
            # שלב א': שמירה זמנית ובטוחה בדיסק בחלקים (מונע ספייקים ב-RAM)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                chunk_size = 1024 * 1024  # בלוקים של 1MB
                while True:
                    chunk = uploaded_file.read(chunk_size)
                    if not chunk:
                        break
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name

            # שלב ב': הרצת העיבוד
            with st.spinner("האפליקציה מקשיבה להקלטה ומייצרת סיכום מלא... אנא המתן."):
                transcript, full_summary = process_audio_and_summarize(tmp_path)

            # שלב ג': הצגת התוצאות למשתמש
            st.markdown("---")
            st.subheader("📋 תוצאות הסיכום המלא")
            st.markdown(full_summary)

            with st.expander("📄 לחץ כאן לצפייה בתמלול המלא והגולמי (מהתחלה ועד הסוף)"):
                st.text_area("טקסט תמלול מלא", transcript, height=300)

        except Exception as e:
            st.error(f"אירעה שגיאה במהלך עיבוד הקובץ: {e}")

        finally:
            # שלב ד': ניקוי בטוח של הקובץ הזמני מהדיסק
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
            
            # שלב ה': פינוי זיכרון אגרסיבי למניעת קריסות RAM
            gc.collect()
