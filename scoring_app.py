import streamlit as st
import pandas as pd
import os
import random
from collections import defaultdict

# ==== CONFIG ====
VIDEO_FOLDER = "videos"
OUTPUT_FILE = "expert_scores.csv"
EXERCISE_GROUPS = ["deadlift", "clean_press", "sprint"]

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
expert_name = st.text_input("Enter your name/ID:")

if expert_name and st.session_state.index < len(st.session_state.video_queue):
    video_path = st.session_state.video_queue[st.session_state.index]
    exercise_type = video_path.split("/")[0]

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
        new_entry = pd.DataFrame([{
            "Expert": expert_name,
            "Video": video_path,
            "Exercise": exercise_type,
            "Form_Label": form_label,
            "Score": score
        }])
        df = pd.read_csv(OUTPUT_FILE)
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_csv(OUTPUT_FILE, index=False)

        # Advance to next video
        st.session_state.index += 1

        # Success message
        st.success("✅ Score saved! Next video loading...")

else:
    if expert_name:
        st.success("🎉 All videos reviewed. Thank you for your evaluation!")
    else:
        st.warning("Please enter your name/ID to begin.")
