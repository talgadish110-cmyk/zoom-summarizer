import os
import streamlit as st

st.title("בדיקת סביבה")

try:
    from google import genai
    import google.genai as g
    st.success(f"google-genai נטען, גרסה: {getattr(g, '__version__', 'לא ידועה')}")
except Exception as e:
    st.error("הספרייה לא נטענת")
    st.exception(e)

try:
    key = st.secrets["GEMINI_API_KEY"]
    st.success(f"המפתח קיים (אורך: {len(key)})")
except Exception as e:
    st.error("המפתח לא מוגדר ב־Secrets")
    st.exception(e)
