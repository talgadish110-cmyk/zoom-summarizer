import time
import json
import requests
import streamlit as st

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

BASE_URL = "https://generativelanguage.googleapis.com"
MODEL = "gemini-2.5-flash"
# מעל הגודל הזה (בבתים) נעדיף להעלות דרך Files API במקום inline base64
INLINE_SIZE_LIMIT = 15 * 1024 * 1024  # 15MB ליתר ביטחון

with st.sidebar:
    st.header("⚙️ הגדרות מערכת")
    if api_key:
        st.success("מפתח ה-API מוגדר במערכת.")
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


import re


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

    # אם גוגל מחזירה עמוד אזהרה (HTML) במקום הקובץ - צריך לאשר עם טוקן
    token = None
    for key, value in response.cookies.items():
        if key.startswith("download_warning"):
            token = value
            break

    if token is None and "text/html" in response.headers.get("Content-Type", ""):
        # ניסיון חלופי: לחלץ את הטוקן מתוך גוף התגובה (Google משנה את זה מדי פעם)
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

    # ניחוש mime type/שם קובץ מתוך הקישור המקורי, בהיעדר מידע טוב יותר מהתגובה
    guessed_mime = content_type if content_type and "octet-stream" not in content_type else "audio/mp3"
    display_name = f"drive_file_{file_id}"

    return file_bytes, guessed_mime, display_name


def gemini_headers():
    """
    כותרות אימות תקניות ל-Gemini API.
    חשוב: זה NOT Bearer token! מפתח Gemini נשלח דרך x-goog-api-key.
    """
    return {"x-goog-api-key": api_key}


def upload_file_to_gemini(file_bytes: bytes, mime_type: str, display_name: str) -> str:
    """
    מעלה קובץ גדול ל-Gemini Files API בפרוטוקול resumable upload,
    ומחזיר את ה-file_uri לשימוש בבקשת generateContent.

    הערה: לנקודת הקצה של ה-Files API (upload/v1beta/files) גוגל דורשת
    את המפתח כפרמטר ?key= בכתובת ה-URL, לא רק כ-header - לכן הוא נשלח בשתי הצורות.
    """
    num_bytes = len(file_bytes)

    # שלב 1: פתיחת סשן העלאה (start)
    start_headers = {
        **gemini_headers(),
        "X-Goog-Upload-Protocol": "resumable",
        "X-Goog-Upload-Command": "start",
        "X-Goog-Upload-Header-Content-Length": str(num_bytes),
        "X-Goog-Upload-Header-Content-Type": mime_type,
        "Content-Type": "application/json",
    }
    start_body = {"file": {"display_name": display_name}}

    start_resp = requests.post(
        f"{BASE_URL}/upload/v1beta/files",
        params={"key": api_key},
        headers=start_headers,
        data=json.dumps(start_body),
    )
    if start_resp.status_code != 200:
        raise RuntimeError(
            f"פתיחת ההעלאה ל-Files API נכשלה (קוד {start_resp.status_code}): {start_resp.text}"
        )

    upload_url = start_resp.headers.get("X-Goog-Upload-URL")
    if not upload_url:
        raise RuntimeError("לא התקבלה כתובת העלאה (X-Goog-Upload-URL) מ-Gemini.")

    # שלב 2: העלאת התוכן בפועל (upload + finalize)
    upload_headers = {
        "Content-Length": str(num_bytes),
        "X-Goog-Upload-Offset": "0",
        "X-Goog-Upload-Command": "upload, finalize",
    }
    upload_resp = requests.post(upload_url, headers=upload_headers, data=file_bytes)
    if upload_resp.status_code != 200:
        raise RuntimeError(
            f"העלאת תוכן הקובץ נכשלה (קוד {upload_resp.status_code}): {upload_resp.text}"
        )

    file_info = upload_resp.json()["file"]
    file_uri = file_info["uri"]
    file_name = file_info["name"]  # לדוגמה: "files/abc123"

    # שלב 3: המתנה שהקובץ יעבור מעיבוד (PROCESSING) למצב פעיל (ACTIVE)
    state = file_info.get("state", "PROCESSING")
    while state == "PROCESSING":
        time.sleep(2)
        status_resp = requests.get(
            f"{BASE_URL}/v1beta/{file_name}", params={"key": api_key}, headers=gemini_headers()
        )
        status_resp.raise_for_status()
        file_info = status_resp.json()
        state = file_info.get("state", "PROCESSING")

    if state != "ACTIVE":
        raise RuntimeError(f"עיבוד הקובץ נכשל בצד גוגל (סטטוס: {state}).")

    return file_uri, file_name


def delete_gemini_file(file_name: str):
    """מוחק את הקובץ שהועלה מהשרתים של גוגל אחרי שסיימנו איתו."""
    try:
        requests.delete(f"{BASE_URL}/v1beta/{file_name}", params={"key": api_key}, headers=gemini_headers())
    except Exception:
        pass  # ניקוי best-effort - אין צורך לעצור את המשתמש בגלל זה


def summarize_with_gemini(prompt: str, mime_type: str, file_bytes: bytes, display_name: str) -> str:
    """
    שולח את הבקשה ל-Gemini. אם הקובץ קטן - שולח inline (base64) בתוך הבקשה.
    אם הקובץ גדול - מעלה אותו קודם דרך Files API ושולח רק הפניה (file_uri).
    """
    file_name_to_cleanup = None

    if len(file_bytes) <= INLINE_SIZE_LIMIT:
        import base64
        base64_audio = base64.b64encode(file_bytes).decode("utf-8")
        parts = [
            {"text": prompt},
            {"inline_data": {"mime_type": mime_type, "data": base64_audio}},
        ]
    else:
        st.info("📤 הקובץ גדול - מעלה אותו דרך Files API (זה עשוי לקחת רגע)...")
        file_uri, file_name_to_cleanup = upload_file_to_gemini(file_bytes, mime_type, display_name)
        parts = [
            {"text": prompt},
            {"file_data": {"mime_type": mime_type, "file_uri": file_uri}},
        ]

    url = f"{BASE_URL}/v1beta/models/{MODEL}:generateContent"
    headers = {**gemini_headers(), "Content-Type": "application/json"}
    payload = {"contents": [{"parts": parts}]}

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    # ניקוי הקובץ מהענן של גוגל, בין אם הצלחנו ובין אם לא
    if file_name_to_cleanup:
        delete_gemini_file(file_name_to_cleanup)

    if response.status_code != 200:
        raise RuntimeError(f"שגיאה מ-Gemini generateContent (קוד {response.status_code}): {response.text}")

    res_json = response.json()
    return res_json["candidates"][0]["content"]["parts"][0]["text"]


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

                except requests.HTTPError as e:
                    st.error(f"שגיאת HTTP מול Google API: {e}")
                except Exception as e:
                    st.error(f"אירעה שגיאה בתהליך הניתוח: {e}")
                    if "401" in str(e) or "403" in str(e) or "UNAUTHENTICATED" in str(e):
                        st.warning(
                            "בדוק שמפתח ה-API שהגדרת ב-Secrets הוא אכן מפתח Gemini "
                            "תקני שהופק דרך Google AI Studio (https://aistudio.google.com/apikey), "
                            "ולא סוד/מפתח OAuth של שירות אחר."
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
        "קבצים גדולים יותר (עד 2GB) מועלים אוטומטית דרך Files API של גוגל, "
        "וזה עשוי לקחת מספר שניות עד דקות בהתאם לגודל הקובץ."
    )
    st.markdown("5. הקובץ נמחק אוטומטית מהשרתים של גוגל (מה-Files API) בסיום העיבוד.")
