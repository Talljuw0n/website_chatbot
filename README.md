# Website Chat Analyzer with LLaMA 3 (Groq API)

This is a Flask-based web application that allows users to:

- 🔗 Enter a website URL
- 🔍 Scrape and clean the website content
- 💬 Ask questions about the website using LLaMA 3 via Groq API

> Built for researchers, analysts, and curious minds who want instant insights from webpages.

---

## Features

- Web scraping of live website content
-  Intelligent content sanitization and truncation
-  LLaMA 3-powered chatbot via Groq Cloud API
-  Memory-based conversation history
-  Error handling for invalid URLs, scraping issues, and API failures
-  Robust validation and logging

---

## Setup Instructions

1. Clone the Repo

```bash
git clone https://github.com/your-username/website-llama-chat.git
cd website-llama-chat

2. Create a Virtual Environment

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install Dependencies
pip install -r requirements.txt

4. Set Up Environment Variables
Create a .env file in the project root:
GROQ_API_KEY=your_groq_api_key_here # or whatever api key you choose to use 

5. Run the App
python app.py
Then go to: http://127.0.0.1:5000

File Structure 
.
├── app.py              # Main Flask backend
├── scraper.py          # Web scraper logic
├── templates/
│   └── index.html      # Frontend UI (optional)
├── .env                # Environment variables
└── requirements.txt    # Python dependencies

How It Works
- Scraping: Accepts a valid URL and extracts readable content (HTML stripped).
-Sanitization: Cleans, truncates, and prepares content for LLM.
-Chat: Sends the content + conversation history to LLaMA 3 via Groq API.
-Response: Displays the AI-generated answer.