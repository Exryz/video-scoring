import streamlit as st
import pandas as pd
import random
import os

# ==== CONFIG ====
VIDEO_CSV = "videos.csv"  # tab or comma delimited with Exercise, Video_Name, URL
OUTPUT_FILE = "expert_scores.csv"

# ==== LOAD VIDEO LIST ====
if not os.path.exists(VIDEO_CSV):
    st.error("❌ videos.csv not found. Please upload the file with Exercise, Video_Name, URL.")
    st.stop()

# Auto-detect separator (tab or comma)
video_df = pd.read_csv(VIDEO_CSV, sep=None, engine="python")
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

# ==== CSV INIT ====
if not os.path.exists(OUTPUT_FILE):
    pd.DataFrame(columns=["Expert", "Video", "Exercise", "Form_Label", "Score"]).to_csv(OUTPUT_FILE, index=False)

# ==== APP ====
st.title("🏋️ Exercise Form Scoring App")
expert_name = st.text_input("Enter your name (e.g., Airnel, Chris, Andrea):")

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

    # Embed Google Drive video with iframe
    if "file/d/" in video_url:
        iframe_code = f'<iframe src="{video_url}" width="640" height="480" allow="autoplay"></iframe>'
    elif "uc?export=download&id=" in video_url:
        file_id = video_url.split("id=")[-1]
        iframe_code = f'<iframe src="https://drive.google.com/file/d/{file_id}/preview" width="640" height="480" allow="autoplay"></iframe>'
    else:
        iframe_code = f'<video width="640" height="480" controls><source src="{video_url}" type="video/mp4"></video>'
    
    st.markdown(iframe_code, unsafe_allow_html=True)

    form_label = st.radio("Form Classification", ["Good Form", "Bad Form"])
    score = st.slider("Form Quality Score (0–100)", 0, 100, 75)

    if st.button("💾 Save & Next(Click twice)"):
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
