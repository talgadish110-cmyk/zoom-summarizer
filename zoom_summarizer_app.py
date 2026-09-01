import time
from google import genai
from google.genai import errors
import pandas as pd
import streamlit as st

# כותרת האפליקציה
st.set_page_config(
    page_title="Control Center & AI Analyzer", page_icon="🛡️", layout="wide"
)

st.title("🛡️ מרכז בקרה ואוטומציה - סייבר ופיתוח")
st.write(
    "ממשק ניהול לניתוח קבצים, הפקת סיכומים והרצת סקריפטים באמצעות Google GenAI."
)

# הגדרת מפתח ה-API (מומלץ לשלוף מ-Streamlit Secrets או להגדיר בצורה בטוחה)
# אפשר להגדיר ב- st.secrets["GEMINI_API_KEY"] או להכניס כאן את המפתח שלך
api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    st.warning("נא להגדיר את מפתח ה-API ב-Streamlit Secrets.")
else:
    # אתחול הלקוח החדש של Google GenAI
    client = genai.Client(api_key=api_key)

    # אזור העלאת קבצים
    uploaded_file = st.file_uploader(
        "העלה קובץ לניתוח (למשל טקסט, קוד או נתונים)",
        type=["txt", "py", "csv", "json", "log"],
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        file_content = file_bytes.decode("utf-8", errors="ignore")

        st.success("הקובץ הועלה בהצלחה!")

        if st.button("התחל ניתוח עמוק והפקת סיכום מורחב"):
            with st.spinner("מנתח את ההקלטה בניתוח מעמקי ומפיק את הסיכום המורחב..."):
                max_retries = 3
                retry_delay = 2
                success = False
                response = None

                # מנגנון ניסיון חוזר במקרה של עומס זמני (שגיאות 503)
                for attempt in range(max_retries):
                    try:
                        # שימוש במודל היציב והמהיר gemini-2.0-flash
                        response = client.models.generate_content(
                            model="gemini-2.0-flash",
                            contents=f"אנא נתח את תוכן הקובץ הבא והקפד על מתן סיכום מפורט ומקצועי בעברית:\n\n{file_content}",
                        )
                        success = True
                        break
                    except errors.APIError as e:
                        if "503" in str(e) or "UNAVAILABLE" in str(e):
                            if attempt < max_retries - 1:
                                time.sleep(retry_delay)
                                retry_delay *= (
                                    2  # המתנה אקספוננציאלית בין ניסיונות
                                )
                                continue
                        st.error(f"אירעה שגיאה בתהליך הניתוח: {e}")
                        break
                    except Exception as e:
                        st.error(fا"שגיאה בלתי צפויה: {e}")
                        break

                if success and response:
                    st.markdown("### תוצאות הניתוח:")
                    st.write(response.text)
