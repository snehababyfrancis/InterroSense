# InterroSense
**Scenario-Based AI-Driven Criminal Interrogation System with Real-Time Micro-Expression Analysis**

## 📌 Overview
InterroSense is an AI-powered interrogation support platform that combines **adaptive conversational AI** with **real-time multimodal deception analysis**.  
It assists law enforcement officers by dynamically adjusting questioning strategies based on both **verbal content** and **non-verbal cues** from suspects.

---

## 🚀 Key Features
- **Scenario-Based Adaptive Questioning**  
  - Fine-tuned Qwen1.5-1.8B-Chat model trained on scenario-rich interrogation datasets.  
  - Adjusts questioning style in real time using suspect’s responses and behavioral cues.

- **Real-Time Facial Cue Analysis**  
  - Micro-expression detection via MobileNetV3-based AU Classifier trained on Bag-of-Lies dataset.  
  - Gaze and head pose tracking to detect avoidance, stress, or deceptive behavior.

- **Multimodal Fusion for Deception Scoring**  
  - Combines linguistic, sentiment, and facial behavioral cues.  
  - Weighted late fusion with real-time modality reliability adjustment.

- **Officer Dashboard (Python Django)**  
  - Live deception probability score and contributing cues.  
  - Suggested next questions and complete conversation logs.

---
