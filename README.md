# 🌟 Gemini Project – LLM Code Deployment App

This project is built as part of the IITM BS Data Science **LLM Code Deployment** evaluation.  
It automates the **build, deploy, and update** process for AI-generated web applications using **FastAPI**, **Gemini LLM**, and **GitHub Pages**.

---

## 🚀 Features

- Accepts POST requests with structured JSON payloads  
- Verifies student secret before processing  
- Generates app code using Gemini API  
- Creates & updates GitHub repositories automatically  
- Enables GitHub Pages deployment  
- Notifies an external evaluation API with repo and deployment metadata  
- Supports multiple rounds (Round 1, Round 2, Round 3…) for iteration  

---

## 🧠 Tech Stack

| Component | Description |
|------------|--------------|
| **Backend** | FastAPI (Python 3.10+) |
| **AI Model** | Gemini LLM |
| **Deployment** | GitHub Pages + Docker |
| **Version Control** | Git & GitHub |
| **Environment** | Hugging Face Spaces |

---

## ⚙️ Setup Instructions

### **1️⃣ Clone the repository**
```bash
git clone https://github.com/24f2006816/gemini-project.git
cd gemini-project
