import streamlit as st
import pandas as pd
import random
import os
from github import Github
from io import StringIO

# ==== CONFIG ====
VIDEO_CSV = "videos.csv"  # tab or comma delimited with Exercise, Video_Name, URL
OUTPUT_FILE = "expert_scores.csv"
GITHUB_FILE_PATH = "expert_scores.csv"

# ==== GITHUB SYNC FUNCTIONS ====
def load_scores_from_github():
    token = st.secrets["GITHUB_TOKEN"]
    repo_name = st.secrets["GITHUB_REPO"]
    branch = st.secrets.get("GITHUB_BRANCH", "main")

    g = Github(token)
    repo = g.get_repo(repo_name)

    try:
        contents = repo.get_contents(GITHUB_FILE_PATH, ref=branch)
        csv_data = contents.decoded_content.decode("utf-8")
        return pd.read_csv(StringIO(csv_data))
    except Exception:
        return pd.DataFrame(columns=["Expert", "Video", "Exercise", "Form_Label", "Score"])

def push_to_github(local_path, commit_message="Update scores"):
    token = st.secrets["GITHUB_TOKEN"]
    repo_name = st.secrets["GITHUB_REPO"]
    branch = st.secrets.get("GITHUB_BRANCH", "main")

    g = Github(token)
    repo = g.get_repo(repo_name)

    # Load local data (just-updated scores)
    local_df = pd.read_csv(local_path)

    try:
        contents = repo.get_contents(GITHUB_FILE_PATH, ref=branch)
        existing_data = contents.decoded_content.decode("utf-8")
        existing_df = pd.read_csv(StringIO(existing_data))

        # Merge & deduplicate
        combined_df = pd.concat([existing_df, local_df], ignore_index=True)
        combined_df.drop_duplicates(subset=["Expert", "Video"], keep="last", inplace=True)

        # Save
        csv_buffer = StringIO()
        combined_df.to_csv(csv_buffer, index=False)

        repo.update_file(
            path=contents.path,
            message=commit_message,
            content=csv_buffer.getvalue(),
            sha=contents.sha,
            branch=branch
        )
        st.success("✅ Scores synced to GitHub (deduplicated).")

    except Exception:
        # File doesn’t exist → create
        csv_buffer = StringIO()
        local_df.to_csv(csv_buffer, index=False)
        repo.create_file(
            path=GITHUB_FILE_PATH,
            message=commit_message,
            content=csv_buffer.getvalue(),
            branch=branch
        )
        st.success("🆕 Created expert_scores.csv in GitHub repo.")

# ==== LOAD VIDEO LIST ====
if not os.path.exists(VIDEO_CSV):
    st.error("❌ videos.csv not found. Please upload the file with Exercise, Video_Name, URL.")
    st.stop()

video_df = pd.read_csv(VIDEO_CSV, sep=None, engine="python")
video_df.columns = video_df.columns.str.strip().str.lower()

required_cols = {"exercise", "video_name", "url"}
if not required_cols.issubset(set(video_df.columns)):
    st.error(f"❌ videos.csv must have columns: {required_cols}. Found: {set(video_df.columns)}")
    st.stop()

# ==== LOAD EXISTING SCORES FROM GITHUB ====
scores_df = load_scores_from_github()

# ==== VIDEO QUEUE ====
if "video_queue" not in st.session_state or not st.session_state.video_queue:
    st.session_state.video_queue = []
    st.session_state.index = 0

st.title("🏋️ Exercise Form Scoring App")
expert_name = st.text_input("Enter your name (e.g., Airnel, Chris, Andrea, Erick):")

if expert_name and not st.session_state.video_queue:
    scored_videos = scores_df[scores_df["Expert"] == expert_name]["Video"].tolist()
    video_list = video_df[~video_df["video_name"].isin(scored_videos)].to_dict("records")
    random.shuffle(video_list)
    st.session_state.video_queue = video_list
    st.session_state.index = 0

# ==== CSV INIT (local cache) ====
if not os.path.exists(OUTPUT_FILE):
    scores_df.to_csv(OUTPUT_FILE, index=False)

# === RUBRICS ===
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

# ==== VIDEO SCORING ====
if expert_name and st.session_state.index < len(st.session_state.video_queue):
    current_video = st.session_state.video_queue[st.session_state.index]
    exercise_type = current_video["exercise"]
    video_url = current_video["url"]
    video_name = current_video["video_name"]

    progress = (st.session_state.index + 1) / len(st.session_state.video_queue)
    st.progress(progress)
    st.caption(f"Progress: {st.session_state.index+1} of {len(st.session_state.video_queue)} videos")

    st.subheader(f"Video {st.session_state.index+1}: {exercise_type} - {video_name}")

    # Embed video
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

    if st.button("💾 Save & Next"):
        # Add new score
        new_entry = pd.DataFrame([{
            "Expert": expert_name,
            "Video": video_name,
            "Exercise": exercise_type,
            "Form_Label": st.session_state.form_label,
            "Score": st.session_state.score
        }])

        # Merge into local CSV
        df = pd.read_csv(OUTPUT_FILE)
        df = pd.concat([df, new_entry], ignore_index=True)
        df.drop_duplicates(subset=["Expert", "Video"], keep="last", inplace=True)
        df.to_csv(OUTPUT_FILE, index=False)

        # Push to GitHub
        push_to_github(OUTPUT_FILE, commit_message=f"{expert_name} scored {video_name}")

        st.success("✅ Score saved & synced! Next video loading...")
        st.session_state.index += 1
        st.rerun()

elif expert_name:
    st.success("🎉 All videos reviewed. Thank you for your evaluation!")
else:
    st.warning("Please enter your name/ID to begin.")

# ==== DOWNLOAD CSV FOR CURRENT EXPERT ====
if expert_name:
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
