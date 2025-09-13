import streamlit as st
import pandas as pd
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ==== CONFIG ====
VIDEO_CSV = "videos.csv"  # tab or comma delimited with Exercise, Video_Name, URL

# ==== GOOGLE SHEETS AUTH ====
def get_gsheet(sheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("artful-shelter-472011-c4-aafeee859c9d.json", scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name).sheet1  # open first sheet

def save_score_to_sheet(expert_name, video_name, exercise_type, form_label, score):
    try:
        sheet = get_gsheet(f"{expert_name}_Scores")  # Match sheet name with expert
        sheet.append_row([expert_name, video_name, exercise_type, form_label, score])
    except Exception as e:
        st.error(f"❌ Could not save to Google Sheets: {e}")

# ==== LOAD VIDEO LIST ====
try:
    video_df = pd.read_csv(VIDEO_CSV, sep=None, engine="python")
except Exception:
    st.error("❌ videos.csv not found or invalid. Please upload the file with Exercise, Video_Name, URL.")
    st.stop()

video_df.columns = video_df.columns.str.strip().str.lower()
required_cols = {"exercise", "video_name", "url"}
if not required_cols.issubset(set(video_df.columns)):
    st.error(f"❌ videos.csv must have columns: {required_cols}. Found: {set(video_df.columns)}")
    st.stop()

if "video_queue" not in st.session_state or not st.session_state.video_queue:
    video_list = video_df.to_dict("records")
    random.shuffle(video_list)
    st.session_state.video_queue = video_list
    st.session_state.index = 0

# ==== APP ====
st.title("🏋️ Exercise Form Scoring App")
expert_name = st.text_input("Enter your name (e.g., Airnel, Chris, Andrea, Erick):")

# === RUBRICS (now in expander for mobile) ===
with st.expander("📖 Scoring Rubrics (tap to expand)"):
    st.markdown("""
    **Form Classification (Good / Bad):**  
    - **Good Form:** Safe and technically sound.  
    - **Bad Form:** Risk of injury, critical errors.  

    **Form Quality Score (0–100):**
    - **90–100 (Excellent):** Textbook execution, no visible errors.  
    - **75–89 (Good):** Minor deviations, overall safe.  
    - **60–74 (Fair):** Noticeable flaws but rep still completed.  
    - **40–59 (Poor):** Significant breakdown in form, unsafe tendencies.  
    - **0–39 (Unsafe):** Major errors, high injury risk, unacceptable form.  
    """)

# ==== Persistent inputs ====
if "form_label" not in st.session_state:
    st.session_state.form_label = "Good Form"
if "score" not in st.session_state:
    st.session_state.score = 75

if expert_name and st.session_state.index < len(st.session_state.video_queue):
    current_video = st.session_state.video_queue[st.session_state.index]
    exercise_type = current_video["exercise"]
    video_url = current_video["url"]
    video_name = current_video["video_name"]

    # Progress bar
    progress = (st.session_state.index + 1) / len(st.session_state.video_queue)
    st.progress(progress)
    st.caption(f"Progress: {st.session_state.index+1} of {len(st.session_state.video_queue)} videos")

    st.subheader(f"Video {st.session_state.index+1}: {exercise_type} - {video_name}")

    # Responsive video embed
    if "file/d/" in video_url:
        iframe_code = f'''
        <div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;max-width:100%;">
            <iframe src="{video_url}" 
                    style="position:absolute;top:0;left:0;width:100%;height:100%;" 
                    frameborder="0" allowfullscreen></iframe>
        </div>'''
    elif "uc?export=download&id=" in video_url:
        file_id = video_url.split("id=")[-1]
        iframe_code = f'''
        <div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;max-width:100%;">
            <iframe src="https://drive.google.com/file/d/{file_id}/preview" 
                    style="position:absolute;top:0;left:0;width:100%;height:100%;" 
                    frameborder="0" allowfullscreen></iframe>
        </div>'''
    else:
        iframe_code = f'''
        <video style="width:100%;height:auto;" controls>
            <source src="{video_url}" type="video/mp4">
        </video>'''
    st.markdown(iframe_code, unsafe_allow_html=True)

    # Input widgets
    st.radio(
        "Form Classification",
        ["Good Form", "Bad Form"],
        index=0 if st.session_state.form_label == "Good Form" else 1,
        key="form_label",
        horizontal=True
    )

    st.slider(
        "Form Quality Score (0–100)",
        0, 100, st.session_state.score,
        key="score"
    )
    st.caption("👉 Slide left = worse form, right = better form")

    if st.button("💾 Save & Next"):
        save_score_to_sheet(expert_name, video_name, exercise_type, st.session_state.form_label, st.session_state.score)
        st.success("✅ Saved to Google Sheets in real-time!")
        st.session_state.index += 1
        st.rerun()

elif expert_name:
    st.success("🎉 All videos reviewed. Thank you for your evaluation!")
else:
    st.warning("Please enter your name/ID to begin.")
