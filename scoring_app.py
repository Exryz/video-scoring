import streamlit as st
import pandas as pd
import random
import os

# ==== CONFIG ====
VIDEO_CSV = "videos.csv"  # tab-delimited file with Exercise, Video_Name, URL
OUTPUT_FILE = "expert_scores.csv"

# ==== FUNCTIONS ====
def convert_to_preview(url):
    """Convert Google Drive download links to preview links."""
    if "uc?export=download&id=" in url:
        file_id = url.split("id=")[-1]
        return f"https://drive.google.com/file/d/{file_id}/preview"
    return url

# ==== LOAD VIDEO LIST ====
if not os.path.exists(VIDEO_CSV):
    st.error("❌ videos.csv not found. Please upload the file with Exercise, Video_Name, URL.")
    st.stop()

# Use auto-detect for delimiter
video_df = pd.read_csv(VIDEO_CSV, sep=None, engine="python")
video_df.columns = video_df.columns.str.strip().str.lower()

# Ensure correct columns exist
required_cols = {"exercise", "video_name", "url"}
if not required_cols.issubset(set(video_df.columns)):
    st.error(f"❌ videos.csv must have columns: {required_cols}. Found: {set(video_df.columns)}")
    st.stop()

# Convert Drive links for playback
video_df["url"] = video_df["url"].apply(convert_to_preview)

if "video_queue" not in st.session_state or not st.session_state.video_queue:
    video_list = video_df.to_dict("records")
    random.shuffle(video_list)
    st.session_state.video_queue = video_list
    st.session_state.index = 0

# ==== CSV INIT ====
if not os.path.exists(OUTPUT_FILE):
    pd.DataFrame(columns=["Expert", "Video", "Exercise", "Form_Label", "Score"]).to_csv(OUTPUT_FILE, index=False)

# ==== APP ====
st.title("🏋️ Exercise Form Scoring App")
expert_name = st.text_input("Enter your name/ID (e.g., EXP01, EXP02, EXP03):")

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
    st.video(video_url)

    form_label = st.radio("Form Classification", ["Good Form", "Bad Form"])
    score = st.slider("Form Quality Score (0–100)", 0, 100, 75)

    if st.button("💾 Save & Next"):
        df = pd.read_csv(OUTPUT_FILE)

        # Check for duplicate entry
        exists = df[(df["Expert"] == expert_name) & (df["Video"] == video_name)]

        if not exists.empty:
            st.warning("⚠️ You already scored this video. Skipping...")
            st.session_state.index += 1
        else:
            new_entry = pd.DataFrame([{
                "Expert": expert_name,
                "Video": video_name,
                "Exercise": exercise_type,
                "Form_Label": form_label,
                "Score": score
            }])
            df = pd.concat([df, new_entry], ignore_index=True)
            df.to_csv(OUTPUT_FILE, index=False)

            st.success("✅ Score saved! Next video loading...")
            st.session_state.index += 1

elif expert_name:
    st.success("🎉 All videos reviewed. Thank you for your evaluation!")
else:
    st.warning("Please enter your name/ID to begin.")

# ==== DOWNLOAD CSV FOR CURRENT EXPERT ====
if expert_name and os.path.exists(OUTPUT_FILE):
    df = pd.read_csv(OUTPUT_FILE)
    expert_df = df[df["Expert"] == expert_name]

    if expert_df.empty:
        st.info("ℹ️ No scores recorded yet for your ID.")
    else:
        csv = expert_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            f"📥 Download Your Scores ({len(expert_df)} entries)",
            csv,
            file_name=f"{expert_name}_scores.csv",
            mime="text/csv"
        )

# ==== RESET DATA OPTION (Admin Use) ====
st.markdown("---")
if st.checkbox("⚠️ Show admin options"):
    if st.button("🔄 Reset Data"):
        pd.DataFrame(columns=["Expert", "Video", "Exercise", "Form_Label", "Score"]).to_csv(OUTPUT_FILE, index=False)
        st.session_state.video_queue = []
        st.session_state.index = 0
        st.success("✅ All data has been reset. Restart the app to begin fresh.")
