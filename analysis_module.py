import cv2
import mediapipe as mp
import numpy as np
import json
import os
import time
from datetime import datetime

# Import the bonus features module
from bonus.analysis_enhancer import BonusAnalyzer

class PoseAnalyzer:
    """
    A class to analyze a cricket cover drive from a video file.
    """
    def __init__(self, input_video_path, output_dir='output'):
        self.input_video_path = input_video_path
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = os.path.join(output_dir, f"analysis_{timestamp}")
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"Saving results to: {self.output_dir}")
        
        self.config = self._load_config()

        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.mp_drawing = mp.solutions.drawing_utils
        self.metrics_over_time = {
            'front_elbow_angle': [], 'spine_lean': [],
            'head_knee_alignment': [], 'front_foot_direction': [],
            'wrist_y_coords': [], 'hip_y_coords': []
        }
        self.phases_per_frame = []

    def _load_config(self):
        """Loads thresholds and reference data from config.json."""
        try:
            with open('config.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Warning: config.json not found. Using default values.")
            return {
                "feedback_thresholds": {"good_elbow_angle": 160, "head_alignment_ratio": 0.5},
                "reference_drive": {
                    "impact_metrics": {
                        "front_elbow_angle": {"min": 165, "max": 180, "weight": 0.4},
                        "spine_lean": {"min": 10, "max": 25, "weight": 0.3}
                    }
                }
            }

    def _calculate_angle(self, a, b, c):
        a = np.array(a); b = np.array(b); c = np.array(c)
        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        if angle > 180.0:
            angle = 360 - angle
        return angle

    def _calculate_metrics(self, landmarks, frame_width, frame_height):
        metrics = {}
        try:
            shoulder = [landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x * frame_width, landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y * frame_height]
            elbow = [landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].x * frame_width, landmarks[self.mp_pose.PoseLandmark.LEFT_ELBOW.value].y * frame_height]
            wrist = [landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].x * frame_width, landmarks[self.mp_pose.PoseLandmark.LEFT_WRIST.value].y * frame_height]
            hip_l = [landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].x * frame_width, landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value].y * frame_height]
            hip_r = [landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value].x * frame_width, landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value].y * frame_height]
            shoulder_l = [landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].x * frame_width, landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].y * frame_height]
            shoulder_r = [landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x * frame_width, landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y * frame_height]
            nose = [landmarks[self.mp_pose.PoseLandmark.NOSE.value].x * frame_width, landmarks[self.mp_pose.PoseLandmark.NOSE.value].y * frame_height]
            knee = [landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].x * frame_width, landmarks[self.mp_pose.PoseLandmark.LEFT_KNEE.value].y * frame_height]
            heel = [landmarks[self.mp_pose.PoseLandmark.LEFT_HEEL.value].x * frame_width, landmarks[self.mp_pose.PoseLandmark.LEFT_HEEL.value].y * frame_height]
            foot_index = [landmarks[self.mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value].x * frame_width, landmarks[self.mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value].y * frame_height]
            
            hip_midpoint = [(hip_l[0] + hip_r[0]) / 2, (hip_l[1] + hip_r[1]) / 2]

            metrics['front_elbow_angle'] = self._calculate_angle(shoulder, elbow, wrist)
            shoulder_midpoint = [(shoulder_l[0] + shoulder_r[0]) / 2, (shoulder_l[1] + shoulder_r[1]) / 2]
            metrics['spine_lean'] = self._calculate_angle(hip_midpoint, shoulder_midpoint, [shoulder_midpoint[0], hip_midpoint[1]])
            shoulder_width = abs(shoulder_l[0] - shoulder_r[0])
            metrics['head_knee_alignment'] = abs(nose[0] - knee[0]) / shoulder_width if shoulder_width > 0 else 0
            metrics['front_foot_direction'] = self._calculate_angle([heel[0] + 100, heel[1]], heel, foot_index)
            metrics['wrist_y_coords'] = wrist[1]
            metrics['hip_y_coords'] = hip_midpoint[1]

        except Exception as e:
            print(f"Error calculating metrics: {e}")
            return None
        return metrics

    def _generate_feedback(self, metrics):
        feedback = {}
        thresholds = self.config['feedback_thresholds']
        if metrics.get('front_elbow_angle', 0) > thresholds['good_elbow_angle']:
            feedback['elbow'] = ("Good elbow extension", (0, 255, 0))
        else:
            feedback['elbow'] = ("Bend elbow more", (0, 0, 255))
        if metrics.get('head_knee_alignment', 1) < thresholds['head_alignment_ratio']:
            feedback['head'] = ("Head over front knee", (0, 255, 0))
        else:
            feedback['head'] = ("Lean head forward", (0, 0, 255))
        return feedback

    def _draw_overlays(self, frame, metrics, feedback, landmarks, current_phase=""):
        self.mp_drawing.draw_landmarks(frame, landmarks, self.mp_pose.POSE_CONNECTIONS, self.mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2), self.mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2))
        frame_height, _, _ = frame.shape
        dashboard_start_y = frame_height - 220
        sub_img = frame[dashboard_start_y:frame_height, 0:450]; white_rect = np.ones(sub_img.shape, dtype=np.uint8) * 50
        res = cv2.addWeighted(sub_img, 0.5, white_rect, 0.5, 1.0); frame[dashboard_start_y:frame_height, 0:450] = res
        
        if current_phase:
            cv2.putText(frame, f"Phase: {current_phase}", (10, dashboard_start_y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 0), 2)

        text_start_y = dashboard_start_y + 70
        if 'front_elbow_angle' in metrics: cv2.putText(frame, f"Elbow Angle: {int(metrics['front_elbow_angle'])} deg", (10, text_start_y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        if 'spine_lean' in metrics: cv2.putText(frame, f"Spine Lean: {int(metrics['spine_lean'])} deg", (10, text_start_y + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        if 'head_knee_alignment' in metrics: cv2.putText(frame, f"Head Align: {metrics['head_knee_alignment']:.2f} (ratio)", (10, text_start_y + 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        if 'elbow' in feedback: cv2.putText(frame, feedback['elbow'][0], (10, text_start_y + 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, feedback['elbow'][1], 2)
        if 'head' in feedback: cv2.putText(frame, feedback['head'][0], (10, text_start_y + 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, feedback['head'][1], 2)
        return frame

    def _generate_final_evaluation(self, impact_frame_index=None):
        evaluation = {}
        avg_foot_angle = np.mean(self.metrics_over_time['front_foot_direction'])
        evaluation['Footwork'] = {'score': 8.5 if 45 < avg_foot_angle < 90 else 4.0, 'feedback': "Ensure the front foot points towards the cover region."}
        good_head_frames = sum(1 for x in self.metrics_over_time['head_knee_alignment'] if x < 0.5)
        evaluation['Head Position'] = {'score': round((good_head_frames / len(self.metrics_over_time['head_knee_alignment'])) * 10, 1), 'feedback': "A stable head over the front knee is crucial for balance."}
        
        if impact_frame_index is not None and impact_frame_index < len(self.metrics_over_time['front_elbow_angle']):
            elbow_at_impact = self.metrics_over_time['front_elbow_angle'][impact_frame_index]
            swing_score = (elbow_at_impact / 180) * 10
            feedback_swing = f"Elbow angle at impact was {int(elbow_at_impact)}°. Aim for full extension."
        else:
            max_elbow_angle = max(self.metrics_over_time['front_elbow_angle'])
            swing_score = (max_elbow_angle / 180) * 10
            feedback_swing = "Aim for a full extension of the front arm through the shot."

        evaluation['Swing Control'] = {'score': round(swing_score, 1), 'feedback': feedback_swing}
        
        spine_lean_std = np.std(self.metrics_over_time['spine_lean'])
        balance_score = max(1, min(10, 10 - (spine_lean_std / 10) * 10))
        evaluation['Balance'] = {'score': round(balance_score, 1), 'feedback': "Maintain a consistent and stable posture."}
        evaluation['Follow-through'] = {'score': 7.5, 'feedback': "A high and complete follow-through ensures commitment."}
        
        return evaluation

    def process_video_first_pass(self):
        """First pass through the video to gather all landmark data without writing video."""
        print("Starting first pass: Data gathering...")
        cap = cv2.VideoCapture(self.input_video_path)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(image)
            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                current_metrics = self._calculate_metrics(landmarks, frame_width, frame_height)
                if current_metrics:
                    for key, value in current_metrics.items():
                        self.metrics_over_time[key].append(value)
        cap.release()
        print("First pass complete.")

    def generate_outputs(self, run_bonus_features=False):
        """Second pass to generate all outputs after data is gathered."""
        print("Starting second pass: Generating outputs...")
        if not self.metrics_over_time['front_elbow_angle']:
            print("No data collected, cannot generate report.")
            return {}

        impact_frame, evaluation, chart_path, html_report_path = None, {}, "", ""
        
        if run_bonus_features:
            # --- THIS IS THE FIX ---
            # Pass self.config to the BonusAnalyzer
            bonus_analyzer = BonusAnalyzer(self.metrics_over_time, self.output_dir, self.config)
            # --- END FIX ---
            impact_frame = bonus_analyzer.find_impact_moment()
            self.phases_per_frame = bonus_analyzer.segment_shot_phases(impact_frame)
            evaluation = self._generate_final_evaluation(impact_frame)
            evaluation = bonus_analyzer.add_skill_grade_to_evaluation(evaluation)
            evaluation = bonus_analyzer.add_reference_comparison(evaluation, impact_frame)
            bonus_analyzer.export_temporal_chart(impact_frame)
            chart_path = os.path.join(self.output_dir, 'elbow_angle_chart.png')
            html_report_path = bonus_analyzer.export_html_report(evaluation, chart_path)
        else:
            evaluation = self._generate_final_evaluation()

        report_path = os.path.join(self.output_dir, 'evaluation.json')
        with open(report_path, 'w') as f:
            json.dump(evaluation, f, indent=4)

        self._write_annotated_video()

        return {
            "video_path": os.path.join(self.output_dir, 'annotated_video.mp4'),
            "report_path": report_path,
            "chart_path": chart_path,
            "evaluation_data": evaluation,
            "html_report_path": html_report_path
        }

    def _write_annotated_video(self):
        """Writes the annotated video file using pre-calculated data."""
        print("Writing annotated video...")
        cap = cv2.VideoCapture(self.input_video_path)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        output_video_path = os.path.join(self.output_dir, 'annotated_video.mp4')
        out = cv2.VideoWriter(output_video_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (frame_width, frame_height))
        
        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(image)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            current_phase = self.phases_per_frame[frame_idx] if frame_idx < len(self.phases_per_frame) else ""
            
            if results.pose_landmarks and frame_idx < len(self.metrics_over_time['front_elbow_angle']):
                metrics = {k: v[frame_idx] for k, v in self.metrics_over_time.items() if len(v) > frame_idx}
                feedback = self._generate_feedback(metrics)
                annotated_frame = self._draw_overlays(image, metrics, feedback, results.pose_landmarks, current_phase)
                out.write(annotated_frame)
            else:
                out.write(frame)
            frame_idx += 1
        
        cap.release()
        out.release()
        self.pose.close()
        print("Annotated video saved.")

def analyze_video(video_path, run_bonus_features=False):
    """
    High-level function to run the full analysis pipeline on a video.
    This function is called by the Streamlit app.
    """
    analyzer = PoseAnalyzer(input_video_path=video_path)
    analyzer.process_video_first_pass()
    results = analyzer.generate_outputs(run_bonus_features)
    return results
