import numpy as np
import matplotlib.pyplot as plt
import os
import base64

class BonusAnalyzer:
    """
    A class to handle all the advanced (bonus) analysis features.
    """
    def __init__(self, metrics_over_time, output_dir, config):
        self.metrics_over_time = metrics_over_time
        self.output_dir = output_dir
        self.config = config

    def find_impact_moment(self):
        wrist_y_coords = self.metrics_over_time.get('wrist_y_coords', [])
        if not wrist_y_coords or len(wrist_y_coords) < 2:
            return None
        velocities = [wrist_y_coords[i] - wrist_y_coords[i-1] for i in range(1, len(wrist_y_coords))]
        impact_frame_index = np.argmax(velocities) + 1 if velocities else None
        print(f"BONUS: Impact detected at frame index: {impact_frame_index}")
        return impact_frame_index

    def segment_shot_phases(self, impact_frame_index):
        """Segments the shot into phases based on wrist and hip movement."""
        if impact_frame_index is None:
            return ["Analysis"] * len(self.metrics_over_time['wrist_y_coords'])

        wrist_y = np.array(self.metrics_over_time['wrist_y_coords'])
        
        # Find the peak of the backswing (highest point, which is min y-value)
        # Search only before the impact frame
        peak_backswing_frame = np.argmin(wrist_y[:impact_frame_index]) if impact_frame_index > 0 else 0

        phases = []
        for i in range(len(wrist_y)):
            if i < peak_backswing_frame:
                phases.append("Backswing")
            elif i < impact_frame_index:
                phases.append("Downswing")
            else:
                phases.append("Follow-through")
        
        # Simple heuristic for Stance: first few frames with little movement
        for i in range(min(10, len(phases))): # Check first 10 frames
             if wrist_y[i] > wrist_y[peak_backswing_frame] * 0.95: # If wrist hasn't moved up much
                 phases[i] = "Stance"
             else:
                 break
        
        print("BONUS: Shot phases segmented.")
        return phases

    def add_skill_grade_to_evaluation(self, evaluation):
        scores = [details['score'] for category, details in evaluation.items() if 'score' in details]
        average_score = np.mean(scores)
        skill_grade = "Beginner"
        if average_score >= 8.0: skill_grade = "Advanced"
        elif average_score >= 6.0: skill_grade = "Intermediate"
        evaluation['Overall Grade'] = {'grade': skill_grade, 'average_score': round(average_score, 2)}
        print(f"BONUS: Overall Skill Grade: {skill_grade} (Avg Score: {average_score:.2f})")
        return evaluation

    def add_reference_comparison(self, evaluation, impact_frame_index):
        """Compares impact metrics to a reference and adjusts the score."""
        if impact_frame_index is None:
            return evaluation

        print("BONUS: Comparing shot to reference drive...")
        reference_metrics = self.config['reference_drive']['impact_metrics']
        total_deviation_score = 0
        total_weight = 0

        # Compare elbow angle
        elbow_ref = reference_metrics['front_elbow_angle']
        elbow_actual = self.metrics_over_time['front_elbow_angle'][impact_frame_index]
        if elbow_ref['min'] <= elbow_actual <= elbow_ref['max']:
            deviation_elbow = 0 # Perfect
        else:
            deviation_elbow = min(abs(elbow_actual - elbow_ref['min']), abs(elbow_actual - elbow_ref['max']))
        
        # Normalize deviation (e.g., 10 degrees off is worse than 2)
        total_deviation_score += (deviation_elbow / 20) * elbow_ref['weight'] # Max 20 deg deviation considered
        total_weight += elbow_ref['weight']

        # Compare spine lean
        spine_ref = reference_metrics['spine_lean']
        spine_actual = self.metrics_over_time['spine_lean'][impact_frame_index]
        if spine_ref['min'] <= spine_actual <= spine_ref['max']:
            deviation_spine = 0
        else:
            deviation_spine = min(abs(spine_actual - spine_ref['min']), abs(spine_actual - spine_ref['max']))
        
        total_deviation_score += (deviation_spine / 15) * spine_ref['weight'] # Max 15 deg deviation
        total_weight += spine_ref['weight']

        # Calculate a final benchmark score (0 to 10)
        # 10 is a perfect match, 0 is high deviation
        benchmark_score = max(0, 10 * (1 - (total_deviation_score / total_weight)))
        
        evaluation['Benchmark Comparison'] = {
            'score': round(benchmark_score, 1),
            'feedback': f"Your shot matched the ideal form with a score of {benchmark_score:.1f}/10."
        }
        return evaluation

    def export_temporal_chart(self, impact_frame_index=None):
        if not self.metrics_over_time.get('front_elbow_angle'):
            print("BONUS: Cannot generate chart, no elbow angle data."); return
        plt.figure(figsize=(10, 6))
        plt.plot(self.metrics_over_time['front_elbow_angle'], label='Front Elbow Angle')
        if impact_frame_index is not None:
            plt.axvline(x=impact_frame_index, color='r', linestyle='--', label=f'Impact Moment (Frame {impact_frame_index})')
        plt.title("Elbow Angle Consistency During Shot")
        plt.xlabel("Frame Number"); plt.ylabel("Angle (Degrees)")
        plt.legend(); plt.grid(True)
        chart_path = os.path.join(self.output_dir, 'elbow_angle_chart.png')
        plt.savefig(chart_path); plt.close()
        print(f"BONUS: Temporal consistency chart saved to {chart_path}")

    def export_html_report(self, evaluation, chart_path):
        """Generates a self-contained HTML report of the analysis."""
        print("BONUS: Generating HTML report...")
        
        # Encode chart image to base64 to embed it in the HTML
        chart_base64 = ""
        try:
            with open(chart_path, "rb") as image_file:
                chart_base64 = base64.b64encode(image_file.read()).decode()
        except Exception as e:
            print(f"Could not embed chart in HTML report: {e}")

        # Build HTML content
        html_content = f"""
        <html>
        <head>
            <title>Cricket Shot Analysis Report</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; background-color: #f4f7f6; }}
                .container {{ max-width: 800px; margin: 20px auto; padding: 20px; background-color: #fff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1, h2 {{ color: #1a2a3a; border-bottom: 2px solid #e1e8ed; padding-bottom: 10px; }}
                .grade {{ text-align: center; margin: 20px 0; }}
                .grade-value {{ font-size: 4em; font-weight: bold; color: #007bff; }}
                .grade-label {{ font-size: 1.2em; color: #5a7894; }}
                .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 20px; }}
                .metric {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 5px solid #007bff; }}
                .metric h3 {{ margin: 0 0 5px 0; color: #1a2a3a; }}
                .metric .score {{ font-size: 2em; font-weight: bold; color: #343a40; }}
                .metric .feedback {{ font-size: 0.9em; color: #6c757d; margin-top: 10px; }}
                .chart {{ text-align: center; margin-top: 30px; }}
                img {{ max-width: 100%; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Cover Drive Analysis Report</h1>
        """

        if 'Overall Grade' in evaluation:
            grade_info = evaluation.pop('Overall Grade')
            html_content += f"""
                <div class="grade">
                    <div class="grade-value">{grade_info['grade']}</div>
                    <div class="grade-label">Overall Grade (Avg Score: {grade_info['average_score']})</div>
                </div>
            """

        html_content += "<h2>Performance Metrics</h2><div class='metrics-grid'>"
        for category, details in evaluation.items():
            html_content += f"""
                <div class="metric">
                    <h3>{category}</h3>
                    <div class="score">{details.get('score', 'N/A')}/10</div>
                    <p class="feedback">{details.get('feedback', '')}</p>
                </div>
            """
        html_content += "</div>"

        if chart_base64:
            html_content += f"""
                <div class="chart">
                    <h2>Temporal Analysis</h2>
                    <img src="data:image/png;base64,{chart_base64}" alt="Elbow Angle Chart">
                </div>
            """
        
        html_content += "</div></body></html>"
        
        report_path = os.path.join(self.output_dir, 'analysis_report.html')
        with open(report_path, 'w') as f:
            f.write(html_content)
        
        print(f"BONUS: HTML report saved to {report_path}")
        return report_path
