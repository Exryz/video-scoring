import streamlit as st
import pandas as pd
import os
import random
from collections import defaultdict

# ==== CONFIG ====
VIDEO_FOLDER = "videos"   # Folder containing exercise subfolders
OUTPUT_FILE = "expert_scores.csv"
EXERCISE_GROUPS = ["deadlift", "clean_press", "sprint"]  # Subfolders under videos/

# Load or initialize scoring progress
if "video_queue" not in st.session_state:
    # Gather videos grouped by exercise
    grouped_videos = defaultdict(list)
    for group in EXERCISE_GROUPS:
        folder_path = os.path.join(VIDEO_FOLDER, group)
        if os.path.exists(folder_path):
            files = [f for f in os.listdir(folder_path) if f.endswith(('.mp4', '.mov', '.avi'))]
            random.shuffle(files)  # Randomize order within group
            grouped_videos[group] = [os.path.join(group, f) for f in files]

    # Shuffle group order
    group_order = EXERCISE_GROUPS[:]
    random.shuffle(group_order)

    # Create a single queue
    video_queue = []
    for group in group_order:
        video_queue.extend(grouped_videos[group])

    st.session_state.video_queue = video_queue
    st.session_state.index = 0

# Initialize CSV if not exists
if not os.path.exists(OUTPUT_FILE):
    pd.DataFrame(columns=["Expert", "Video", "Exercise", "Form_Label", "Score"]).to_csv(OUTPUT_FILE, index=False)

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

    if st.button("Save Score"):
        # Save entry
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

        # Confirm saved
        st.success(f"✅ Score saved for {video_path}")

        # Add "Next Video" button
        if st.button("➡️ Next Video"):
            st.session_state.index += 1
            st.experimental_set_query_params()  # lightweight refresh
else:
    if expert_name:
        st.success("🎉 All videos reviewed. Thank you for your evaluation!")
    else:
        st.warning("Please enter your name/ID to begin.")
