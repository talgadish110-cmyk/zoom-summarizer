import os
import streamlit as st
from groq import Groq
from streamlit_mic_recorder import mic_recorder

st.set_page_config(
    page_title="מערכת תמלול וסיכום שיעורים אמיתית",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
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
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-header">🎙️ מערכת תמלול וסיכום שיעורים אמיתית (Whisper)</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-header">המערכת מאזינה לקובץ האודיו שלך מילה במילה, מתמללת אותו, ומסכמת אך ורק את מה שנאמר בשיעור!</div>',
    unsafe_allow_html=True,
)

# שליפת מפתח Groq מתוך ה-Secrets
secret_groq_key = st.secrets.get("GROQ_API_KEY", "")

with st.sidebar:
    st.header("⚙️ הגדרות מערכת")
    api_key = st.text_input(
        "הכנס מפתח Groq API (מתחיל ב-gsk_)", value=secret_groq_key, type="password"
    )
    
    if api_key:
        st.success("מפתח ה-API מוגדר במערכת.")
    else:
        st.warning("נא להזין מפתח Groq.")

    st.markdown("---")
    st.markdown("### 📋 סוג הסיכום המבוקש")
    summary_type = st.selectbox(
        "בחר פורמט סיכום",
        [
            "סיכום מלא מהתחלה ועד הסוף (מפורט ורציף)",
            "סיכום מנהלים מקיף",
            "נקודות עיקריות ואקשן איטמס (Action Items)",
            "תמלול מלא עם תובנות",
            "סיכום לפי נושאים כרונולוגיים",
        ],
    )

tab1, tab2 = st.tabs(["📁 העלאת קובץ שיעור (MP3/WAV/M4A)", "🎙️ הקלטה ישירה מהמיקרופון"])

with tab1:
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("### 📥 העלאת קובץ מהמחשב")
        uploaded_file = st.file_uploader(
            "בחר קובץ אודיו (MP3, WAV, M4A)",
            type=["mp3", "wav", "m4a", "mp4", "mpeg"],
        )
        if uploaded_file:
            st.info(f"📁 קובץ נטען: {uploaded_file.name} ({uploaded_file.size / (1024*1024):.2f} MB)")

    with col2:
        st.markdown("### 🤖 תמלול וסיכום אמיתי")

        if st.button("התחל תמלול וניתוח ההקלטה", type="primary", key="btn_file"):
            if not api_key:
                st.error("אנא הכנס מפתח Groq API בסרגל הצד או ב-Secrets.")
            elif uploaded_file is None:
                st.warning("אנא בחר או העלה קובץ אודיו תחילה.")
            else:
                try:
                    client = Groq(api_key=api_key)
                    
                    # שמירת קובץ זמני
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name

                    st.info("🔄 שלב 1/2: שולח את קובץ האודיו לתמלול חכם (Whisper)... פעולה זו עשויה לקחת דקה לקבצים גדולים.")

                    # תמלול אמיתי דרך Whisper
                    with open(tmp_path, "rb") as audio_file:
                        transcription_obj = client.audio.transcriptions.create(
                            file=(uploaded_file.name, audio_file.read()),
                            model="whisper-large-v3",
                            prompt="השיעור מתנהל בעברית. נא לתמלל בעברית בצורה מדויקת ומלאה.",
                            response_format="text",
                            language="he"
                        )
                    
                    os.unlink(tmp_path)
                    transcribed_text = transcription_obj
                    
                    if not transcribed_text or len(transcribed_text.strip()) < 3:
                        st.error("לא זוהה דיבור ברור בקובץ. ודא שהקובץ מכיל אודיו תקין.")
                    else:
                        st.info("🧠 שלב 2/2: מעבד את הטקסט המתומלל ומייצר סיכום מדויק לשיעור...")

                        # סיכום מבוסס תמלול אמיתי בלבד דרך Llama 3
                        summary_prompt = f"""
                        להלן תמלול מדויק של שיעור או פגישה שהתקיימה:
                        ---
                        {transcribed_text}
                        ---
                        
                        על בסיס התמלול הזה בלבד, צור עבורי סיכום מקצועי ומפורט בעברית לפי הפורמט הבא: {summary_type}.
                        הקפד להציג אך ורק את התכנים, המושגים והנושאים שהוזכרו במפורש בתמלול, ואל תמציא פרטים חיצוניים.
                        """

                        chat_completion = client.chat.completions.create(
                            messages=[
                                {
                                    "role": "system",
                                    "content": "אתה עוזר אקדמי מקצועי שמסכם הרצאות אך ורק על סמך התמלול האמיתי שסופק.",
                                },
                                {
                                    "role": "user",
                                    "content": summary_prompt,
                                }
                            ],
                            model="llama-3.3-70b-versatile",
                        )

                        summary_text = chat_completion.choices[0].message.content

                        st.success("השיעור התומלל וסוכם בהצלחה מלאה!")
                        
                        st.markdown("---")
                        st.markdown("### 📝 תוצאות הסיכום לשיעור")
                        st.markdown(summary_text)

                        with st.expander("🔍 הצג את התמלול המלא (מה המרצה אמר מילה במילה)"):
                            st.write(transcribed_text)

                        st.download_button(
                            label="📥 הורד סיכום כקובץ טקסט",
                            data=summary_text,
                            file_name="lesson_summary.txt",
                            mime="text/plain",
                        )

                except Exception as e:
                    st.error(f"אירעה שגיאה בתהליך התמלול: {e}")

with tab2:
    st.markdown("### 🎙️ הקלטה קולית חיה")
    audio_recorded = mic_recorder(
        start_prompt="🔴 התחל הקלטה",
        stop_prompt="⏹️ עצור הקלטה",
        just_once=False,
        key="mic_recorder"
    )

    if audio_recorded:
        st.audio(audio_recorded['bytes'], format='audio/wav')
        
        if st.button("תמלל וסכם הקלטה חיה", type="primary", key="btn_mic"):
            if not api_key:
                st.error("אנא הכנס מפתח Groq API בסרגל הצד.")
            else:
                try:
                    client = Groq(api_key=api_key)
                    st.info("🔄 מתמלל את ההקלטה שלך...")

                    transcription_obj = client.audio.transcriptions.create(
                        file=("mic_audio.wav", audio_recorded['bytes']),
                        model="whisper-large-v3",
                        response_format="text",
                        language="he"
                    )

                    transcribed_text = transcription_obj

                    summary_prompt = f"""
                    להלן תמלול של הקלטה קולית:
                    ---
                    {transcribed_text}
                    ---
                    סכם את התוכן בעברית לפי הפורמט: {summary_type}.
                    """

                    chat_completion = client.chat.completions.create(
                        messages=[{"role": "user", "content": summary_prompt}],
                        model="llama-3.3-70b-versatile",
                    )

                    summary_text = chat_completion.choices[0].message.content

                    st.success("ההקלטה סוכמה בהצלחה!")
                    st.markdown("---")
                    st.markdown("### 📝 תוצאות הסיכום")
                    st.markdown(summary_text)

                    with st.expander("🔍 הצג את התמלול המלא"):
                        st.write(transcribed_text)

                except Exception as e:
                    st.error(f"שגיאה: {e}")
