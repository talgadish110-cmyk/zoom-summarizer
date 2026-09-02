import os
import streamlit as st
from groq import Groq
from google import genai
import tempfile
import math
import time
from streamlit_mic_recorder import mic_recorder

st.set_page_config(
    page_title="מערכת תמלול וסיכום עם Gemini",
    page_icon="🎙️",
    layout="wide"
)

st.title("🎙️ מערכת תמלול אמיתי (Whisper) וסיכום רחב (Gemini)")
st.write("השמעת הקלטות או קבצי זום כבדים, תמלול מדויק מילה במילה, וסיכום אקדמי רחב ועמוק באמצעות Gemini!")

# שדות להכנסת המפתחות (ריקים מבחינה אבטחתית כדי לא לחשוף בגיטהאב)
col_keys1, col_keys2 = st.columns(2)
with col_keys1:
    groq_api_key = st.text_input(
        "הכנס מפתח Groq API החדש שלך:", 
        value="", 
        type="password",
        placeholder="gsk_..."
    )
with col_keys2:
    gemini_api_key = st.text_input(
        "הכנס מפתח Google API:", 
        value="", 
        type="password",
        placeholder="AQ.Ab8RN..."
    )

col1, col2 = st.columns(2)

with col1:
    st.subheader("📁 העלאת קובץ להאזנה וסיכום רחב")
    uploaded_file = st.file_uploader("בחירת קובץ אודיו (MP3, WAV, M4A)", type=["mp3", "wav", "m4a"])

    if uploaded_file is not None and groq_api_key and gemini_api_key:
        file_size_mb = uploaded_file.size / (1024 * 1024)
        st.info(f"📁 קובץ נטען: {uploaded_file.name} ({file_size_mb:.2f} MB)")

        if st.button("התחל תמלול וסיכום רחב עם Gemini", type="primary"):
            try:
                client = Groq(api_key=groq_api_key)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name

                file_bytes = uploaded_file.getvalue()
                total_size = len(file_bytes)
                
                chunk_size = 10 * 1024 * 1024
                num_chunks = math.ceil(total_size / chunk_size)

                st.info(f"✂️ מפצל את הקובץ ל-{num_chunks} חלקים לצורך תמלול מלא מדויק...")

                full_transcript = []
                progress_bar = st.progress(0)

                for i in range(num_chunks):
                    start_byte = i * chunk_size
                    end_byte = min((i + 1) * chunk_size, total_size)
                    chunk_data = file_bytes[start_byte:end_byte]

                    chunk_filename = f"chunk_{i}.mp3"
                    st.text(f"מתמלל חלק {i+1} מתוך {num_chunks}...")

                    res = client.audio.transcriptions.create(
                        file=(chunk_filename, chunk_data),
                        model="whisper-large-v3",
                        language="he",
                        response_format="text"
                    )
                    full_transcript.append(res)
                    progress_bar.progress((i + 1) / num_chunks)
                    time.sleep(1.5)

                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

                transcribed_text = "\n".join(full_transcript)

                if not transcribed_text or len(transcribed_text.strip()) < 3:
                    st.error("לא זוהה דיבור ברור בקובץ.")
                else:
                    st.success("✅ התמלול המלא הושלם בהצלחה! מעביר לניתוח וסיכום רחב ב-Gemini...")

                    g_client = genai.Client(api_key=gemini_api_key)

                    prompt = f"""
                    אתה עוזר אקדמי ומקצועי בכיר. להלן תמלול מלא של שיעור/הקלטה שהתקבל ממערכת תמלול. 
                    אנא צור עבורי סיכום רחב, מקיף, מעמיק ומפורט מאוד בעברית. 
                    הסיכום צריך לכלול:
                    1. מבוא וסקירה כללית של הנושאים המרכזיים שעלו.
                    2. פירוט מעמיק של התכנים לפי סדר הדברים (כולל מושגים מקצועיים, הסברים ודוגמאות אם הוזכרו).
                    3. תובנות מרכזיות או החלטות שהתקבלו.
                    4. סיכום פעולות או משימות המשך (Action Items) אם ישנן.

                    להלן התמלול המלא לניתוח:
                    {transcribed_text}
                    """

                    with st.spinner("🧠 Gemini מייצר עבורך סיכום רחב ומעמיק..."):
                        response = g_client.models.generate_content(
                            model='gemini-3.6-flash',
                            contents=prompt,
                        )
                        summary = response.text

                    st.markdown("---")
                    st.markdown("### 📋 סיכום רחב ומקיף מאת Gemini")
                    st.markdown(summary)

                    with st.expander("🔍 הצג את התמלול המלא שהופק"):
                        st.write(transcribed_text)

                    st.download_button(
                        label="📥 הורד סיכום כקובץ טקסט",
                        data=summary,
                        file_name="gemini_comprehensive_summary.txt",
                        mime="text/plain"
                    )

            except Exception as e:
                st.error(f"שגיאה בתהליך: {e}")

with col2:
    st.subheader("🎙️ הקלטה ישירה מהמיקרופון")
    audio_recorded = mic_recorder(
        start_prompt="🔴 התחל הקלטה",
        stop_prompt="⏹️ עצור הקלטה",
        just_once=False,
        key="mic_recorder"
    )

    if audio_recorded and groq_api_key and gemini_api_key:
        st.audio(audio_recorded['bytes'], format='audio/wav')
        
        if st.button("תמלל וסכם הקלטה חיה עם Gemini"):
            try:
                client = Groq(api_key=groq_api_key)
                with st.spinner("מתמלל הקלטה חיה..."):
                    res = client.audio.transcriptions.create(
                        file=("mic_audio.wav", audio_recorded['bytes']),
                        model="whisper-large-v3",
                        response_format="text",
                        language="he"
                    )
                
                g_client = genai.Client(api_key=gemini_api_key)
                
                with st.spinner("Gemini מייצר סיכום..."):
                    response = g_client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=f"סכם בהרחבה ובצורה מקצועית את קטע הדיבור הבא בעברית:\n{res}"
                    )
                    summary = response.text

                st.success("התהליך הושלם בהצלחה!")
                st.markdown(summary)
            except Exception as e:
                st.error(f"שגיאה: {e}")
