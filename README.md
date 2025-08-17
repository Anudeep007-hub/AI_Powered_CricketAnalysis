# Real-Time Cricket Cover Drive Analysis: A Deep Dive

This project is a Python-based system I built to analyze the biomechanics of a cricket cover drive from a video. In this document, I'll explain in detail how the system works, from the underlying logic to the mathematical formulas I used for scoring.

---

## 1. How It Works: An Explanation for Everyone

Imagine you have a super-smart digital coach who can watch a video of a batsman and instantly measure their technique. That's exactly what I built this program to do.

Think of it like this:

### The Coach's Eyes (Pose Estimation)

First, my program watches the video, frame by frame. On each frame, I use a tool called MediaPipe Pose to identify and track 33 key points on the batsman's body (like their shoulders, elbows, knees, etc.). It's like I'm putting tiny digital markers on all the important joints.

### The Coach's Tools (Metric Calculation)

Once the markers are in place, I use virtual tools—a protractor and a ruler—to take measurements. I calculate angles (like how bent the elbow is) and distances (like how far the head is from the front knee).

### The Coach's Verdict (Scoring & Feedback)

Finally, I compare these measurements against a "textbook perfect" cover drive.

* If the player's elbow is nice and straight, I give a high score for **Swing Control**.
* If the player's head is stable and over their front foot, I give a high score for **Head Position and Balance**.

This feedback is shown live on the video and summarized in a final report card (`evaluation.json`) that I generate.

In short, I designed the program to translate the visual art of a cover drive into objective, measurable numbers, making it easy to track progress and identify areas for improvement.

---

## 2. How I Score: The Formulas Explained

To score the cover drive, I focus on key principles of batting technique. I've tied each principle to a simple, logical formula.

### Swing Control Score

This measures how straight the front arm gets, which is crucial for power.

**Formula:**

```
Score = (Maximum Elbow Angle / 180) * 10
```

**Logic:** A perfectly straight arm has an angle of 180°. This formula calculates what percentage of "perfect" the player achieved and converts it to a score out of 10. A higher angle means a better score.

---

### Head Position Score

This rewards players for keeping their head steady and over their front knee, which is vital for balance.

**Formula:**

```
Score = (Percentage of Frames with Good Alignment) * 10
```

**Logic:** I check the head's alignment on every frame. This score is based on how consistently the player maintained the correct head position throughout the shot. Consistency is key, so I reward the percentage of time they did it right.

---

### Balance Score

This measures how stable the player's posture is. A wobbly player is an unbalanced one.

**Formula:**

```
Score = 10 - (Wobble Factor)
```

**Logic:** I calculate a "Wobble Factor" based on how much the player's spine angle changes during the shot. A player who is very still will have a low Wobble Factor and thus a high Balance Score. A player who sways a lot will have a high Wobble Factor and a lower score.

---

### Footwork Score

This is a simple check to see if the front foot is pointing in the right direction (towards the "cover" fielding position).

**Formula:**

```
Score = 8.5 (if correct) or 4.0 (if incorrect)
```

**Logic:** This is a foundational element. If the foot is pointing correctly (between 45° and 90° relative to the batting crease), the player gets a good base score. If not, the score is lower because this fundamental error affects the entire shot.

---

## 3. The Math Behind the Magic: A Deeper Dive

Here, I'll explore why I use these specific mathematical methods. My goal was to choose methods that are not only accurate but also fast and reliable, just like a real coach's intuition.

---

### The Challenge: Measuring Angles from Pixels

A video is just a series of pictures made of pixels. My first challenge was to turn the pixel positions of a player's joints into a meaningful angle.

Let's take the **Elbow Angle**. I have three points: Shoulder (A), Elbow (B), and Wrist (C). I need to find the angle at point B.

---

### Why I Use arctan2 (And Not High School Geometry)

You might remember the "Law of Cosines" from math class, which can find an angle if you know the lengths of the triangle's sides. While this works, it has two drawbacks for my purpose:

1. It's computationally slower.
2. It only gives an angle between 0° and 180°. It can't tell the difference between a joint bending forwards or backwards.

This is why I use a trigonometric function called **arctan2** (or Arc Tangent 2).

---

### How arctan2 Thinks

Imagine drawing a horizontal line through the elbow. arctan2 first calculates the angle of the line from the elbow to the shoulder (Angle 1). Then, it calculates the angle of the line from the elbow to the wrist (Angle 2).

The final angle is simply the difference between these two measurements:

```
Elbow Angle = Angle 2 - Angle 1
```

**Why It's Better:**
This method is extremely fast and robust. It understands a full 360° circle, so it never gets confused about the direction of the bend. It gives me a precise and reliable measurement on every single frame.

---

### The Challenge: Measuring "Wobble" or "Balance"

How can you measure something as abstract as "balance" with a number? A balanced player is a stable player. An unbalanced player is "wobbly." My goal is to measure this "wobbliness."

---

### Why I Use Standard Deviation

**1. Collect the Data:** First, I measure the spine\_lean angle on every frame of the video. This gives me a list of numbers, for example:

```
[20°, 21°, 20°, 23°, 22°]
```

**2. Find the Average:** I find the average of this list. In the example above, the average is **21.2°**.

**3. Measure the "Spread":** Now, I need to know how far each number in the list is from that average. Standard Deviation is a statistical tool that does exactly this. It calculates a single number that represents the "spread" or "dispersion" of the data.

---

### Examples

* **A Low Standard Deviation (e.g., 0.8):**
  This means most of the spine angles were very close to the average. The player's posture was consistent and stable. This is good balance.

Example Data:

```
[20, 21, 20, 21, 20]
```

* **A High Standard Deviation (e.g., 5.2):**
  This means the angles were all over the place, far from the average. The player's posture was inconsistent and shaky. This is poor balance.

Example Data:

```
[15, 25, 18, 28, 20]
```

By using standard deviation, I can convert the complex idea of "balance" into a single, meaningful "Wobble Factor" that accurately reflects the player's stability during the shot.
