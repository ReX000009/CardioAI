 🫀 CardioAI - Cardiovascular Risk Assessment

> Biohackathon 2026 | Conversational AI for Cardiovascular Risk Prediction

## Overview
CardioAI is an AI-powered conversational tool that helps licensed medical professionals assess cardiovascular risk through natural language. Just describe a patient case and CardioAI will gather the necessary information and provide a structured risk assessment.

## Features
- 🗣️ **Fully Conversational** — No forms, no uploads, just chat
- 📊 **Live Risk Dashboard** — Sidebar updates automatically with risk score and factors
- ⚡ **Powered by Groq** — Ultra-fast LLaMA 3.3 70B model
- 🏥 **Evidence-Based** — Follows ACC/AHA and ESC guidelines
- 🔒 **Research Tool** — Built for licensed medical professionals

## How to Use
1. Enter your Groq API key in the sidebar
2. Describe a patient case or ask a cardiology question
3. CardioAI will ask follow-up questions and provide a risk assessment

## Example Prompts
- *"58-year-old male, BP 145/90, LDL 165, smoker, no prior CVD. What's his risk?"*
- *"What are ACC/AHA thresholds for starting statin therapy?"*
- *"Female, 52, post-menopausal, family history of MI, BMI 29"*

## Tech Stack
- **Frontend:** Streamlit
- **AI Model:** LLaMA 3.3 70B via Groq API
- **Language:** Python

## Installation (Local)
```bash
pip install streamlit groq
streamlit run app.py
```

## Disclaimer
> ⚠️ This tool is for **licensed medical professionals only**.  
> It is a **research/trial tool** and **not a diagnostic instrument**.  
> Always consult clinical judgment and established guidelines.

## Built By
ReX000009 | Biohackathon 2026
"""
