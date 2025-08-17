# AI-Powered Cricket Cover Drive Analysis

This project is a Python-based system to analyze the biomechanics of a cricket cover drive from a video. It uses **pose estimation, mathematical metrics, and scoring formulas** to provide detailed feedback on a player’s technique.

---

## 1. How It Works: An Explanation for Everyone

Imagine you have a super-smart digital coach who can watch a video of a batsman and instantly measure their technique. That’s exactly what this system does.

* **The Coach's Eyes (Pose Estimation)**
  Each video is processed frame by frame using **MediaPipe Pose**, which tracks **33 body key points** (shoulders, elbows, knees, etc.) like tiny digital markers.

* **The Coach's Tools (Metric Calculation)**
  Using these key points, the system measures **angles** (e.g., elbow bend) and **distances** (e.g., head position relative to knee).

* **The Coach's Verdict (Scoring & Feedback)**
  These measurements are compared against a “textbook perfect” cover drive. Scores are given for swing control, head position, balance, and footwork.
  A **report card (`evaluation.json`)** and **live video feedback** are generated.

---

## 2. How I Score: The Formulas Explained

The scoring system is built around simple, logical formulas tied to batting principles.

### 🔹 Swing Control Score

* **What it measures:** How straight the front arm is.
* **Formula:**
  `Score = (Maximum Elbow Angle / 180) * 10`
* **Logic:** A perfectly straight arm = 180°. Higher angle → higher score.

### 🔹 Head Position Score

* **What it measures:** Head stability over the front knee.
* **Formula:**
  `Score = (Percentage of Frames with Good Alignment) * 10`
* **Logic:** Consistency across frames is rewarded.

### 🔹 Balance Score

* **What it measures:** Player stability (posture wobble).
* **Formula:**
  `Score = 10 - (Wobble Factor)`
* **Logic:** Based on **spine angle standard deviation**. Lower wobble = higher score.

### 🔹 Footwork Score

* **What it measures:** Correct front foot pointing direction.
* **Formula:**
  `Score = 8.5 (if correct) or 4.0 (if incorrect)`
* **Logic:** Correct foot angle (45°–90°) = good base, else penalty.

---

## 3. The Math Behind the Magic

### Measuring Angles with `arctan2`

* **Why not Law of Cosines?** Slower, limited to 0–180°.
* **Why `arctan2`?** Fast, handles full 360°, distinguishes direction of bend.
* **Example (Elbow Angle):**

  ```
  Elbow Angle = arctan2(wrist - elbow) - arctan2(shoulder - elbow)
  ```

### Measuring Balance with Standard Deviation

* Collect **spine lean angles** across frames.
* Compute **average** and **standard deviation**:

  * Low std. dev. → stable posture (good balance).
  * High std. dev. → shaky posture (poor balance).
* This produces the **Wobble Factor**.

---

## 4. Setup & Run Instructions

###  Prerequisites

* [Anaconda](https://www.anaconda.com/) or Miniconda (recommended), or Python 3.8+
* Git

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd <your-repo-directory>

# Create conda environment
conda create -n mp-env python=3.10 -y
conda activate mp-env

# Install dependencies
pip install -r requirements.txt
```

### ▶ Run the Application

```bash
streamlit run app.py
```

The browser will open a new tab with the application running.

---

## 5. Notes on Assumptions & Limitations

* **Player Handedness:** Currently optimized for **right-handed batsmen**. Left-hand analysis requires inverted logic.
* **Camera Angle:** Works best with a **side-on stable view**.
* **No Bat Tracking:** Focused on **body biomechanics only**.
* **Heuristic-Based Analysis:** Phase segmentation relies on heuristics, not direct measurements.
* **Two-Pass Video Processing:** Slightly less efficient but ensures accurate phase marking.

---

##  Output

* **Live feedback overlay on video**
* **Evaluation JSON report card** with scores for swing control, head position, balance, and footwork

---

## Summary

This project transforms the **art of batting technique** into **objective, measurable metrics**. By combining **pose estimation, math, and scoring logic**, it acts like a **digital batting coach**—helping players track progress and improve their cover drives.
