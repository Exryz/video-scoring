import streamlit as st
import pandas as pd
import os
import random
from collections import defaultdict

# ==== CONFIG ====
video_df = pd.read_csv("videos.csv")  # contains Exercise, Video_Name, URL
if "video_queue" not in st.session_state or not st.session_state.video_queue:
    video_list = video_df.to_dict("records")
    random.shuffle(video_list)
    st.session_state.video_queue = video_list
    st.session_state.index = 0

current_video = st.session_state.video_queue[st.session_state.index]
exercise_type = current_video["Exercise"]
video_url = current_video["URL"]

st.video(video_url)


# ==== SESSION STATE INIT ====
if "video_queue" not in st.session_state:
    st.session_state.video_queue = []
if "index" not in st.session_state:
    st.session_state.index = 0

# ==== BUILD VIDEO QUEUE IF EMPTY ====
if not st.session_state.video_queue:
    grouped_videos = defaultdict(list)
    for group in EXERCISE_GROUPS:
        folder_path = os.path.join(VIDEO_FOLDER, group)
        if os.path.exists(folder_path):
            files = [f for f in os.listdir(folder_path) if f.endswith(('.mp4', '.mov', '.avi'))]
            random.shuffle(files)
            grouped_videos[group] = [os.path.join(group, f) for f in files]

    group_order = EXERCISE_GROUPS[:]
    random.shuffle(group_order)

    video_queue = []
    for group in group_order:
        video_queue.extend(grouped_videos[group])

    st.session_state.video_queue = video_queue

# ==== CSV INIT ====
if not os.path.exists(OUTPUT_FILE):
    pd.DataFrame(columns=["Expert", "Video", "Exercise", "Form_Label", "Score"]).to_csv(OUTPUT_FILE, index=False)

# ==== APP UI ====
st.title("🏋️ Exercise Form Scoring App")
expert_name = st.text_input("Enter your name/ID (e.g., EXP01, EXP02, EXP03):")

if expert_name and st.session_state.index < len(st.session_state.video_queue):
    video_path = st.session_state.video_queue[st.session_state.index]
    exercise_type = video_path.split("/")[0]

    # Progress bar
    progress = (st.session_state.index + 1) / len(st.session_state.video_queue)
    st.progress(progress)
    st.caption(f"Progress: {st.session_state.index+1} of {len(st.session_state.video_queue)} videos")

    st.subheader(f"Video {st.session_state.index+1} of {len(st.session_state.video_queue)}")
    st.video(os.path.join(VIDEO_FOLDER, video_path))

    form_label = st.radio(
        "Form Classification",
        options=["Good Form", "Bad Form"],
        key=f"label_{st.session_state.index}"
    )

    score = st.slider(
        "Form Quality Score (0–100)",
        0, 100, 75,
        key=f"score_{st.session_state.index}"
    )

    if st.button("💾 Save & Next", key=f"save_{st.session_state.index}"):
        df = pd.read_csv(OUTPUT_FILE)

        # Check for duplicate entry
        exists = df[
            (df["Expert"] == expert_name) & 
            (df["Video"] == video_path)
        ]

        if not exists.empty:
            st.warning("⚠️ You already scored this video. Skipping to next...")
            st.session_state.index += 1
        else:
            # Save new entry
            new_entry = pd.DataFrame([{
                "Expert": expert_name,
                "Video": video_path,
                "Exercise": exercise_type,
                "Form_Label": form_label,
                "Score": score
            }])
            df = pd.concat([df, new_entry], ignore_index=True)
            df.to_csv(OUTPUT_FILE, index=False)

            st.success("✅ Score saved! Next video loading...")
            st.session_state.index += 1

else:
    if expert_name:
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
        # Clear CSV
        pd.DataFrame(columns=["Expert", "Video", "Exercise", "Form_Label", "Score"]).to_csv(OUTPUT_FILE, index=False)
        
        # Reset session state
        st.session_state.video_queue = []
        st.session_state.index = 0

        st.success("✅ All data has been reset. Restart the app to begin fresh.")
