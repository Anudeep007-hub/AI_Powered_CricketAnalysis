import streamlit as st
import os
import tempfile
from  analysis_module import analyze_video # Import the refactored analysis function

st.set_page_config(page_title="Cricket Shot Analyzer", layout="wide")

st.title("🏏 AI-Powered Cricket Cover Drive Analysis")
st.write("Upload a video of a cover drive to get a detailed biomechanical analysis, frame-by-frame overlays, and a final performance score.")

# --- UI Components ---
uploaded_file = st.file_uploader("Choose a video file...", type=["mp4", "mov", "avi"])
run_bonus = st.checkbox("Enable Advanced Bonus Analysis (Slower)", value=True)

if uploaded_file is not None:
    # Create a temporary file to save the uploaded video
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tfile:
        tfile.write(uploaded_file.read())
        video_path = tfile.name

    st.video(video_path)

    if st.button("Analyze Shot", type="primary"):
        with st.spinner("Analyzing video... This may take a few moments. Please wait."):
            try:
                # Run the analysis function
                results = analyze_video(video_path, run_bonus_features=run_bonus)
                
                st.success("Analysis Complete!")

                # --- Display Results ---
                st.header("Results")
                
                # Display HTML report if available
                if run_bonus and os.path.exists(results.get('html_report_path', '')):
                    st.subheader("Analysis Report")
                    with open(results['html_report_path'], 'r', encoding='utf-8') as f:
                        st.components.v1.html(f.read(), height=600, scrolling=True)
                    with open(results['html_report_path'], "rb") as file:
                        st.download_button(
                            label="Download HTML Report",
                            data=file,
                            file_name="analysis_report.html",
                            mime="text/html"
                        )
                else: # Fallback to basic display
                    st.subheader("Evaluation Report")
                    if results.get('evaluation_data'):
                        eval_data = results['evaluation_data']
                        if 'Overall Grade' in eval_data:
                            grade_info = eval_data.pop('Overall Grade')
                            st.metric(label="Overall Grade", value=grade_info['grade'], delta=f"Avg Score: {grade_info['average_score']}")
                        for category, details in eval_data.items():
                            st.metric(label=category, value=f"{details['score']}/10")
                            st.caption(details['feedback'])
                
                st.subheader("Annotated Video")
                if os.path.exists(results['video_path']):
                    video_file = open(results['video_path'], 'rb')
                    video_bytes = video_file.read()
                    st.video(video_bytes)
                    with open(results['video_path'], "rb") as file:
                        st.download_button(
                            label="Download Annotated Video",
                            data=file,
                            file_name="annotated_video.mp4",
                            mime="video/mp4"
                        )
                else:
                    st.error("Could not find the annotated video file.")

            except Exception as e:
                st.error(f"An error occurred during analysis: {e}")
            finally:
                # Clean up the temporary file
                if os.path.exists(video_path):
                    os.remove(video_path)
