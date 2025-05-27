## 🩺YSHY – Your Smart Healthcare Yardstick

A secure, bilingual (English/Hindi) Streamlit app powered by Gemini, designed to empower women in rural areas to privately assess and manage intimate health concerns.

---

## 🚀 Features

* **Image & Symptom Input**: Upload clear images of intimate areas or describe symptoms in text.
* **AI-Powered Diagnosis**: Gemini-driven preliminary analysis and disease detection.
* **Personalized Care Advice**: Tailored solutions, daily precautions, and self-care tips.
* **Downloadable Reports**: Generate and download your health assessment and history.
* **History Tracking**: Securely store and review previous diagnoses.
* **Clinic Locator**: Find nearby hospitals, clinics, and healthcare centers on demand.
* **Bilingual Support**: Switch seamlessly between English and हिन्दी.
* **Privacy & Security**: End-to-end encryption; data never leaves your device without consent.

---

## 🛠️ Technology Stack

* **Frontend & App**: [Streamlit](https://streamlit.io/)
* **AI Engine**: Google Gemini
* **Languages**: Python 3.9+

---

## 📂 Folder Structure

```
├── app.py             # Main Streamlit entry point
├── pages
│   ├── English.py     # English interface and logic
│   └── हिन्दी.py       # Hindi interface and logic
├── requirements.txt   # Python dependencies
└── README.md          # Project overview
```

---

## ⚙️ Installation & Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/<your-username>/YSHY.git
   cd YSHY
   ```
2. **Create a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   venv\\Scripts\\activate # Windows
   ```
3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```
4. **Configure Gemini API Key**

   ```bash
   export GEMINI_API_KEY=your_api_key_here
   ```

---

## ▶️ Running the App

```bash
streamlit run app.py
```

Open **[http://localhost:8501](http://localhost:8501)** in your browser. Choose English or हिन्दी from the sidebar to begin.

---

## 🔒 Privacy & Data Security

* All data is processed locally by default.
* Uploaded images and reports are stored securely and can be deleted anytime.
* No personal data is shared without explicit user consent.

---

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

1. Fork the repo
2. Create a feature branch
3. Commit your changes
4. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
