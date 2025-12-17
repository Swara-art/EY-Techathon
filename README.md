# 🏥 Serendale – Intelligent Provider Verification Platform (EY Techathon)

![EY Techathon](https://img.shields.io/badge/EY-Techathon-purple)
![AI Powered](https://img.shields.io/badge/AI-Agentic%20AI-blue)
![Healthcare](https://img.shields.io/badge/Domain-Digital%20Health-success)

---

## 📌 Problem Statement: India’s Healthcare “Ghost Network” Crisis

India faces a **critical doctor shortage** (≈7 doctors per 10,000 people), yet digital healthcare directories are riddled with **"ghost providers"** — outdated, incorrect, or fake listings.

### 🚨 Why this is a serious problem

* **Patients** waste time, wages, and money travelling to non-existent or unavailable providers
* **Insurers & TPAs** lose lakhs in manual verification and delayed claim settlements
* **Digital platforms** suffer from fake reviews and pay-for-placement models
* **Healthcare data** is fragmented with no single source of truth

This crisis erodes trust in India’s rapidly growing digital health ecosystem.

---

## 💡 Our Solution: Serendale

**Serendale** acts as the **intelligence layer** for India’s Digital Health Mission (ABDM).

We do **not replace** existing systems — we **bring them to life** by making provider data:

* ✅ Dynamic
* ✅ Self-verifying
* ✅ Continuously updated
* ✅ Trustworthy

At its core, Serendale uses **Agentic AI** to autonomously validate, enrich, and monitor healthcare provider data.

Here are some images of website:
![WhatsApp Image 2025-12-17 at 22 50 36 (1)](https://github.com/user-attachments/assets/becbf9d8-42c0-4662-87e0-8586d16bafd1)

![WhatsApp Image 2025-12-17 at 22 50 37](https://github.com/user-attachments/assets/1b2b8aef-fdf9-4359-a9a9-cbce1b654d6e)


![WhatsApp Image 2025-12-17 at 22 50 38](https://github.com/user-attachments/assets/00f4a039-843a-44e6-9075-0849ed1441b4)



---

## 🧠 How It Works

### 1️⃣ Anchor in Trust

* Uses **Healthcare Professionals Registry (HPR)** as the foundational source of provider identity
* Ensures government-verified authenticity

### 2️⃣ Autonomous Validation

* AI agents work **24/7** to cross-verify:

  * Phone numbers
  * Addresses
  * Practice status
* Validation happens using public data sources and APIs

### 3️⃣ Intelligent Monitoring & Prediction

* AI detects patterns that indicate **future data decay**
* Multilingual NLP analyzes patient reviews to flag real-world issues early

🎯 **Result:** More than **85%+ verified accuracy** in provider directories

---

## 🏗️ System Architecture

Serendale follows a **modular, scalable, and agent-driven architecture**:

* **API Gateway:** FastAPI
* **Task Scheduler:** Celery
* **Agentic AI Core:** LangGraph

  * Validation Agent
  * Enrichment Agent
  * Compliance Risk Agent
  * Directory Management Agent
  * QA Agent
* **LLM Layer:** OpenAI API (Language & Vision Models)
* **Database:** MongoDB

AI agents are orchestrated through a central **AI Orchestrator** that ensures data accuracy and consistency.
<img width="740" height="359" alt="Screenshot 2025-12-17 230330" src="https://github.com/user-attachments/assets/970c5e15-c39d-4cfa-815f-88fd1e729551" />



---

## 🛠️ Tech Stack

### 🔹 Backend

* FastAPI
* Celery

### 🔹 AI & Machine Learning

* LangGraph (Agent orchestration)
* OpenAI API (LLM / NLP / Vision)
* Scikit-learn (confidence scoring & classification)

### 🔹 Data Collection

* Web Scraping: BeautifulSoup, Requests
* External APIs:

  * NPI Registry API
  * Google Maps API
  * State Medical Board APIs

### 🔹 Frontend
* HTML
* Tailwind CSS
* ReactJS

### 🔹 Reporting & Visualization

* Matplotlib

### 🔹 Database & Deployment

* MongoDB
* Docker

  <img width="733" height="460" alt="Screenshot 2025-12-17 230338" src="https://github.com/user-attachments/assets/12db244d-5ebc-47d8-be79-be059a219204" />


---

## 👥 Key Stakeholders & Users

* **Patients** – Access verified healthcare providers
* **Insurance Companies & TPAs** – Reduce manual verification costs
* **Digital Health Platforms** – Improve trust and credibility
* **Government Bodies** – Strengthen ABDM data reliability

---

## 🚀 Impact & Benefits

* ⏱️ Reduced patient effort and financial loss
* 💰 Significant cost savings for insurers
* 🔒 Restored trust in digital health platforms
* 📊 Cleaner, standardized healthcare datasets

---

## 🔮 Future Enhancements

* Voice-based verification agents
* Regional language expansion
* Real-time dashboards for insurers & regulators
* Predictive risk alerts for provider inactivity

---

## 🏆 Hackathon Context

This project was developed as part of **EY Techathon**, focusing on solving real-world challenges using **AI, data intelligence, and scalable system design**.

---

## 📄 License

This project is for **hackathon and academic demonstration purposes**.

---

✨ *Serendale envisions a future where healthcare data is trusted, intelligent, and always up to date.*
