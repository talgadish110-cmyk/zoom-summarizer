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
st.write("העלה את קובץ ה־MP3 של ההקלטה וקבל סיכום מלא מהתחלה ועד הסוף בלי לפספס דבר.")

# העלאת קובץ MP3 (או קבצי אודיו נתמכים נוספים)
uploaded_file = st.file_uploader(
    "בחר קובץ MP3 של ההקלטה", 
    type=["mp3", "wav", "m4a"]
)

def chunk_text(text, max_chars=12000):
    """חיתוך טקסט ארוך למקטעים כדי שלא נחרוג ממגבלת הזיכרון של המודל"""
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]

def process_full_audio_and_summarize(file_path):
    """
    מעבד את קובץ האודיו מהדיסק, מייצר תמלול מלא,
    מנתח אותו מקטע אחר מקטע, ומחזיר סיכום מלא ורציף מהתחלה ועד הסוף.
    """
    st.info("שלב 1/3: מעבד וקורא את קובץ האודיו מהדיסק המקומי...")
    
    # --- כאן תבצע את קריאת ה-API האמיתית שלך לתמלול (לדוגמה OpenAI Whisper API) ---
    # with open(file_path, "rb") as audio_file:
    #     transcript_response = client.audio.transcriptions.create(
    #         model="whisper-1", 
    #         file=audio_file
    #     )
    # full_transcript = transcript_response.text
    
    # סימולציה לצורך הדוגמה (החלף בתמלול האמיתי שלך מתוך ה-API):
    full_transcript = "כאן יופיע כל טקסט התמלול המלא של פגישת ה־Zoom מהרגע הראשון ועד הסוף..." * 40

    st.info("שלב 2/3: מנתח את התמלול ומחלק למקטעים לעיבוד מקיף...")
    chunks = chunk_text(full_transcript)
    
    partial_summaries = []
    for i, chunk in enumerate(chunks):
        # --- כאן תשלח כל מקטע נפרד ל-AI לקבלת סיכום ביניים ---
        # response = client.chat.completions.create(
        #     model="gpt-4o-mini",
        #     messages=[{"role": "user", "content": f"סכם בקצרה את החלק הבא מתוך הפגישה (חלק {i+1}):\n{chunk}"}]
        # )
        # partial_summaries.append(response.choices[0].message.content)
        
        # סימולציה לסיכומי ביניים:
        partial_summaries.append(f"עיקרי חלק {i+1}: דיון על הנושאים המרכזיים שהוצגו בשלב זה.")

    st.info("שלב 3/3: מאחד את כל החלקים ומייצר סיכום־על סופי מהתחלה ועד הסוף...")
    
    # שלב האיחוד (Reduce): גיבוש סיכום רציף ומסודר שכולל את כל תכולת הפגישה
    combined_text = "\n".join(partial_summaries)
    
    # --- כאן תשלח את סיכומי הביניים למודל לקבלת סיכום־על סופי ---
    
    final_summary = f"""
    ### 🎯 סיכום מקיף וכולל של פגישת ה־Zoom (מהתחלה ועד הסוף)
    
    * **היקף הניתוח:** ההקלטה פוצלה ועובדה דרך {len(chunks)} מקטעים מרכזיים כדי לוודא ששום פרט לא פוספס.
    * **נקודות מרכזיות שעלו בדיון:**
      1. סקירת פתיחה והצגת הנושאים שעל הפרק.
      2. ניתוח מעמיק של הנתונים, המשימות והסטטוסים השוטפים.
      3. החלטות מרכזיות שנקבעו לקראת המשך העבודה (Action Items).
      
    *(סיכום זה נוצר מניתוח עומק רציף של כל קובץ ה־MP3 שהועלה).*
    """

    return full_transcript, final_summary

if uploaded_file is not None:
    file_size_mb = uploaded_file.size / (1024 * 1024)
    st.success(f"הקובץ '{uploaded_file.name}' הועלה בהצלחה (גודל: {file_size_mb:.2f} MB)")
    
    if st.button("התחל תמלול וסיכום מלא מהתחלה ועד הסוף"):
        tmp_path = None
        try:
            # שלב א': שמירה זמנית ובטוחה בדיסק בחלקים (מונע ספייקים ב-RAM)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                chunk_size = 1024 * 1024  # כתיבה בבלוקים של 1MB
                while True:
                    chunk = uploaded_file.read(chunk_size)
                    if not chunk:
                        break
                    tmp_file.write(chunk)
                tmp_path = tmp_file.name

            # שלב ב': הרצת התהליך המלא
            with st.spinner("האפליקציה מקשיבה להקלטה ומפיקה סיכום מלא... אנא המתן."):
                transcript, full_summary = process_full_audio_and_summarize(tmp_path)

            # שלב ג': הצגת התוצאות הסופיות במסך
            st.markdown("---")
            st.subheader("📋 תוצאות הסיכום המלא")
            st.markdown(full_summary)

            with st.expander("📄 לחץ כאן לצפייה בתמלול המלא והגולמי (מההתחלה ועד הסוף)"):
                st.text_area("טקסט תמלול", transcript, height=300)

        except Exception as e:
            st.error(f"אירעה שגיאה במהלך עיבוד הקובץ: {e}")

        finally:
            # שלב ד': ניקוי קפדני של הקובץ הזמני מהדיסק
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
            
            # שלב ה': פינוי זיכרון אגרסיבי למניעת דליפות RAM
            gc.collect()
