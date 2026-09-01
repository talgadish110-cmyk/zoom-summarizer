import io
import re
import time
import requests
import streamlit as st

from google import genai
from google.genai import types

st.set_page_config(
    page_title="מערכת סיכום הקלטות זום חכמה",
    page_icon="🎥",
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
    '<div class="main-header">🎥 מערכת חכמה לסיכום הקלטות זום (וידאו ואודיו)</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="sub-header">העלה קובץ אודיו, ותן לבינה המלאכותית לסכם עבורך את הכל!</div>',
    unsafe_allow_html=True,
)

# שליפת המפתח מתוך ה-Secrets שלך
api_key = st.secrets.get("GEMINI_API_KEY", "")

MODEL = "gemini-2.5-flash"
# מעל הגודל הזה נעדיף להעלות דרך Files API (client.files.upload) במקום inline bytes
INLINE_SIZE_LIMIT = 15 * 1024 * 1024  # 15MB ליתר ביטחון

with st.sidebar:
    st.header("⚙️ הגדרות מערכת")
    if api_key:
        masked = api_key[:6] + "····" if len(api_key) > 6 else "····"
        st.success(f"מפתח ה-API מוגדר במערכת ({masked}).")
    else:
        st.error("חסר מפתח ב-Secrets.")

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

tab1, tab2 = st.tabs(["📁 העלאת קובץ / דרייב", "📖 הוראות"])


@st.cache_resource(show_spinner=False)
def get_client(key: str):
    """יוצר Client יחיד של ה-SDK הרשמי, לפי מפתח ה-API. ה-SDK מטפל באימות בעצמו."""
    return genai.Client(api_key=key)


def extract_drive_file_id(url: str) -> str:
    """
    מחלץ את מזהה הקובץ מכל צורה נפוצה של קישור גוגל דרייב, למשל:
    - https://drive.google.com/file/d/FILE_ID/view?usp=sharing
    - https://drive.google.com/open?id=FILE_ID
    - https://drive.google.com/uc?id=FILE_ID
    """
    patterns = [
        r"/file/d/([a-zA-Z0-9_-]+)",
        r"[?&]id=([a-zA-Z0-9_-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError("לא הצלחתי לזהות מזהה קובץ בתוך הקישור. ודא שזה קישור שיתוף תקין של גוגל דרייב.")


def download_from_google_drive(url: str):
    """
    מוריד קובץ מגוגל דרייב לפי קישור שיתוף ציבורי ("כל מי שיש לו את הקישור").
    מטפל גם במקרה של קבצים גדולים (מעל כ-100MB) שגוגל מציגה עבורם
    אזהרת "לא ניתן לסרוק את הקובץ לאיתור וירוסים" עם כפתור אישור.
    מחזיר (file_bytes, mime_type, display_name).
    """
    file_id = extract_drive_file_id(url)
    session = requests.Session()
    base = "https://drive.google.com/uc"

    response = session.get(base, params={"id": file_id, "export": "download"}, stream=True)

    token = None
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            token = value
            break

    if token is None and "text/html" in response.headers.get("Content-Type", ""):
        match = re.search(r'confirm=([0-9A-Za-z_-]+)&', response.text)
        if match:
            token = match.group(1)

    if token:
        response = session.get(
            base, params={"id": file_id, "export": "download", "confirm": token}, stream=True
        )

    if response.status_code != 200:
        raise RuntimeError(f"הורדה מגוגל דרייב נכשלה (קוד {response.status_code}). ודא שהקישור ציבורי.")

    content_type = response.headers.get("Content-Type", "")
    if "text/html" in content_type:
        raise RuntimeError(
            "התקבל דף HTML במקום קובץ. ודא שהרשאת השיתוף מוגדרת ל'כל מי שיש לו את הקישור', "
            "ושמדובר בקישור לקובץ יחיד ולא לתיקייה."
        )

    file_bytes = response.content
    guessed_mime = content_type if content_type and "octet-stream" not in content_type else "audio/mp3"
    display_name = f"drive_file_{file_id}"

    return file_bytes, guessed_mime, display_name


def summarize_with_gemini(prompt: str, mime_type: str, file_bytes: bytes, display_name: str) -> str:
    """
    שולח את הבקשה ל-Gemini דרך ה-SDK הרשמי (google-genai).
    קובץ קטן -> נשלח כ-bytes inline. קובץ גדול -> מועלה קודם דרך client.files.upload
    ואז מוחק אותו מהענן של גוגל בסיום, בין אם הצליח ובין אם לא.
    """
    client = get_client(api_key)
    uploaded_file_name = None

    try:
        if len(file_bytes) <= INLINE_SIZE_LIMIT:
            content_part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
        else:
            st.info("📤 הקובץ גדול - מעלה אותו דרך Files API (זה עשוי לקחת רגע)...")
            uploaded = client.files.upload(
                file=io.BytesIO(file_bytes),
                config=types.UploadFileConfig(display_name=display_name, mime_type=mime_type),
            )
            uploaded_file_name = uploaded.name

            # המתנה שהקובץ יעבור ממצב עיבוד (PROCESSING) למצב פעיל (ACTIVE)
            while uploaded.state == types.FileState.PROCESSING:
                time.sleep(2)
                uploaded = client.files.get(name=uploaded_file_name)

            if uploaded.state != types.FileState.ACTIVE:
                raise RuntimeError(f"עיבוד הקובץ נכשל בצד גוגל (סטטוס: {uploaded.state}).")

            content_part = types.Part.from_uri(file_uri=uploaded.uri, mime_type=mime_type)

        response = client.models.generate_content(
            model=MODEL,
            contents=[prompt, content_part],
        )
        return response.text

    finally:
        if uploaded_file_name:
            try:
                client.files.delete(name=uploaded_file_name)
            except Exception:
                pass  # ניקוי best-effort - לא צריך לעצור את המשתמש בגלל זה


with tab1:
    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("### 📥 מקור הקובץ")
        source_type = st.radio(
            "בחר מאיפה להביא את הקובץ",
            ["מהמחשב שלי", "קישור מגוגל דרייב"],
            horizontal=True,
        )

        uploaded_file = None
        drive_url = ""

        if source_type == "מהמחשב שלי":
            uploaded_file = st.file_uploader(
                "בחר קובץ אודיו (MP3, WAV או M4A)",
                type=["mp3", "wav", "m4a"],
            )
            if uploaded_file is not None:
                size_mb = len(uploaded_file.getvalue()) / (1024 * 1024)
                st.caption(f"גודל קובץ: {size_mb:.1f}MB")
        else:
            drive_url = st.text_input(
                "הדבק כאן קישור שיתוף לקובץ מגוגל דרייב",
                placeholder="https://drive.google.com/file/d/XXXXXXXXXXXX/view?usp=sharing",
            )
            st.caption(
                "⚠️ ודא שהרשאת השיתוף של הקובץ מוגדרת ל'כל מי שיש לו את הקישור', "
                "אחרת ההורדה תיכשל."
            )

    with col2:
        st.markdown("### 🤖 עיבוד וסיכום")

        if st.button("התחל ניתוח וסיכום פגישה", type="primary", key="btn_file"):
            if not api_key:
                st.error("אנא הגדר מפתח ב-Secrets.")
            elif source_type == "מהמחשב שלי" and uploaded_file is None:
                st.warning("אנא בחר או העלה קובץ אודיו תחילה.")
            elif source_type == "קישור מגוגל דרייב" and not drive_url.strip():
                st.warning("אנא הדבק קישור לקובץ בגוגל דרייב.")
            else:
                try:
                    if source_type == "מהמחשב שלי":
                        file_bytes = uploaded_file.getvalue()
                        mime_type = uploaded_file.type if uploaded_file.type else "audio/mp3"
                        display_name = uploaded_file.name
                    else:
                        st.info("📥 מוריד את הקובץ מגוגל דרייב...")
                        file_bytes, mime_type, display_name = download_from_google_drive(drive_url.strip())
                        size_mb = len(file_bytes) / (1024 * 1024)
                        st.caption(f"הקובץ ירד בהצלחה מדרייב ({size_mb:.1f}MB)")

                    st.info("🔄 מעבד את הקובץ ושולח ל-Gemini...")

                    prompt = f"""
                    אתה עוזר אקדמי מקצועי. ניתנת לך הקלטת שיעור / פגישה.
                    אנא צור עבורי סיכום מפורט, מסודר ומעמיק לפי הפורמט הבא: {summary_type}.

                    הנחיות:
                    1. סקור את עיקרי הדברים בצורה רציפה וכרונולוגית מרכזית.
                    2. כלול את המושגים המרכזיים, ההסברים וההחלטות שעלו בשיעור.
                    3. שמור על מבנה נקי, מקצועי וברור בעברית.
                    """

                    summary_text = summarize_with_gemini(
                        prompt=prompt,
                        mime_type=mime_type,
                        file_bytes=file_bytes,
                        display_name=display_name,
                    )

                    st.success("הניתוח והסיכום הושלמו בהצלחה!")
                    st.markdown("---")
                    st.markdown("### 📝 תוצאות הסיכום")
                    st.markdown(summary_text)

                    st.download_button(
                        label="📥 הורד סיכום כקובץ טקסט",
                        data=summary_text,
                        file_name="meeting_summary.txt",
                        mime="text/plain",
                    )

                except Exception as e:
                    st.error(f"אירעה שגיאה בתהליך הניתוח: {e}")
                    if "401" in str(e) or "403" in str(e) or "UNAUTHENTICATED" in str(e) or "PERMISSION" in str(e):
                        st.warning(
                            "בדוק שמפתח ה-API שהגדרת ב-Secrets תקין ופעיל, ושה-Generative Language API "
                            "מופעל בפרויקט שאליו הוא משויך ב-Google Cloud Console."
                        )

with tab2:
    st.markdown("### 📖 מדריך הרצה מהיר")
    st.markdown("1. המפתח שלך מוגדר ב-Secrets תחת השם `GEMINI_API_KEY`.")
    st.markdown(
        "2. בחר את מקור הקובץ - העלאה ישירה מהמחשב, או קישור לקובץ בגוגל דרייב."
    )
    st.markdown(
        "3. לשימוש בקישור מגוגל דרייב: לחץ קליק ימני על הקובץ בדרייב ← "
        "**שיתוף** ← ודא שההרשאה מוגדרת ל'**כל מי שיש לו את הקישור**' ← העתק את הקישור והדבק אותו באפליקציה."
    )
    st.markdown(
        "4. קבצים קטנים (עד כ-15MB) נשלחים ישירות בתוך הבקשה. "
        "קבצים גדולים יותר (עד 2GB) מועלים אוטומטית דרך ה-SDK הרשמי של גוגל, "
        "וזה עשוי לקחת מספר שניות עד דקות בהתאם לגודל הקובץ."
    )
    st.markdown("5. הקובץ נמחק אוטומטית מהשרתים של גוגל בסיום העיבוד.")
    st.markdown("---")
    st.markdown(
        "**דרישת התקנה:** ודא שהחבילה `google-genai` מותקנת (ולא רק `requests`). "
        "הוסף שורה `google-genai` לקובץ `requirements.txt` שלך."
    )
