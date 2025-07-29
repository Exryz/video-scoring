import streamlit as st
import pandas as pd
import os
    
# Folder where segmented videos are stored
VIDEO_FOLDER = "videos"  
OUTPUT_FILE = "expert_scores.csv"

# Load list of videos
videos = [f for f in os.listdir(VIDEO_FOLDER) if f.endswith(('.mp4', '.mov', '.avi'))]

st.title("Exercise Form Scoring App")
st.write("Please review each video and provide your evaluation.")

# Initialize storage for scores if file doesn't exist
if not os.path.exists(OUTPUT_FILE):
    pd.DataFrame(columns=["Expert", "Video", "Form_Label", "Score"]).to_csv(OUTPUT_FILE, index=False)

# Expert input
expert_name = st.text_input("Enter your name/ID:")

if expert_name:
    for video in videos:
        st.subheader(f"Video: {video}")
        st.video(os.path.join(VIDEO_FOLDER, video))

        # Scoring controls
        form_label = st.radio(
            f"Form classification for {video}",
            options=["Good Form", "Bad Form"],
            key=f"{video}_label"
        )

        score = st.slider(
            f"Form quality score for {video} (0 = poor, 100 = perfect)",
            0, 100, 75,
            key=f"{video}_score"
        )

        # Save scores
        if st.button(f"Save score for {video}", key=f"{video}_save"):
            new_entry = pd.DataFrame([{
                "Expert": expert_name,
                "Video": video,
                "Form_Label": form_label,
                "Score": score
            }])
            df = pd.read_csv(OUTPUT_FILE)
            df = pd.concat([df, new_entry], ignore_index=True)
            df.to_csv(OUTPUT_FILE, index=False)
            st.success(f"Saved scores for {video}!")

    st.success("All videos reviewed. Thank you for your evaluation!")
