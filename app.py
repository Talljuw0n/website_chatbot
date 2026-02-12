from flask import Flask, render_template, request, jsonify
from scraper import scrape_website
import requests
import os
import re
from urllib.parse import urlparse
from dotenv import load_dotenv
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

app = Flask(__name__)

def is_valid_url(url):
    """Validate URL format and scheme"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except:
        return False

def sanitize_content(content):
    """Clean and prepare scraped content for AI processing"""
    if not content:
        return ""
    
    # Remove excessive whitespace and normalize
    content = re.sub(r'\s+', ' ', content.strip())
    
    # Limit content length to prevent API limits (adjust as needed)
    max_length = 15000  # Adjust based on your model's context window
    if len(content) > max_length:
        content = content[:max_length] + "..."
        logger.info(f"Content truncated to {max_length} characters")
    
    return content

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({"error": "No URL provided"}), 400
        
        # Validate URL format
        if not is_valid_url(url):
            return jsonify({"error": "Invalid URL format. Please include http:// or https://"}), 400
        
        logger.info(f"Scraping URL: {url}")
        
        # Scrape the website
        raw_content = scrape_website(url)
        
        if not raw_content:
            return jsonify({"error": "Could not extract content from the website. The site may be protected or unavailable."}), 400
        
        # Clean and prepare content
        content = sanitize_content(raw_content)
        
        if len(content) < 50:  # Minimum content threshold
            return jsonify({"error": "Website contains insufficient content to analyze."}), 400
        
        logger.info(f"Successfully scraped {len(content)} characters from {url}")
        
        return jsonify({
            "content": content,
            "url": url,
            "scraped_at": datetime.now().isoformat(),
            "content_length": len(content)
        })
        
    except Exception as e:
        logger.error(f"Error scraping website: {str(e)}")
        return jsonify({"error": "Failed to scrape website. Please check the URL and try again."}), 500

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        history = data.get('history', [])
        context = data.get('context', '')

        if not history:
            return jsonify({"error": "No conversation history provided"}), 400
            
        if not context:
            return jsonify({"error": "No website content available. Please scrape a website first."}), 400

        # Validate history format
        for msg in history:
            if not isinstance(msg, dict) or 'role' not in msg or 'content' not in msg:
                return jsonify({"error": "Invalid message format in history"}), 400

        logger.info(f"Processing chat request with {len(history)} messages")

        # Create enhanced system prompt
        system_prompt = {
            "role": "system",
            "content": f"""You are an AI assistant specialized in analyzing website content and answering questions about it. 

WEBSITE CONTENT:
{context}

INSTRUCTIONS:
- Answer questions based solely on the provided website content
- Be helpful, accurate, and conversational
- If information isn't available in the content, politely say so
- Provide specific details and examples when possible
- Keep responses clear and well-structured
- If asked about topics not covered in the website, redirect to what information is available"""
        }

        # Prepare messages for the API
        messages = [system_prompt] + history

        # Get response from AI
        answer = ask_llama_with_history(messages)
        
        if not answer:
            return jsonify({"error": "Could not generate a response. Please try again."}), 500

        logger.info("Successfully generated AI response")
        
        return jsonify({
            "answer": answer,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({"error": "An error occurred while processing your question. Please try again."}), 500

def ask_llama_with_history(messages):
    """Send chat request to Groq API with improved error handling"""
    try:
        if not GROQ_API_KEY:
            logger.error("GROQ_API_KEY not found in environment variables")
            return "Configuration error: API key not available."

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1024,
            "top_p": 0.9,
            "stream": False
        }

        logger.info("Sending request to Groq API")
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions", 
            headers=headers, 
            json=data,
            timeout=30
        )
        
        if response.status_code == 401:
            logger.error("Invalid API key")
            return "Authentication error: Please check your API key configuration."
        
        if response.status_code == 429:
            logger.error("Rate limit exceeded")
            return "I'm currently experiencing high demand. Please try again in a moment."
        
        if not response.ok:
            logger.error(f"API request failed with status {response.status_code}: {response.text}")
            return "I'm having trouble connecting to my AI service. Please try again later."

        result = response.json()
        
        if 'choices' not in result or not result['choices']:
            logger.error("Invalid API response format")
            return "I received an unexpected response. Please try again."
            
        return result['choices'][0]['message']['content']
        
    except requests.exceptions.Timeout:
        logger.error("API request timeout")
        return "The request timed out. Please try again with a shorter question."
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error: {str(e)}")
        return "I'm having network connectivity issues. Please try again."
    
    except Exception as e:
        logger.error(f"Unexpected error in ask_llama_with_history: {str(e)}")
        return "An unexpected error occurred while generating a response."

# Legacy endpoint for backward compatibility (though not used by the new UI)
@app.route('/ask', methods=['POST'])
def ask():
    """Legacy endpoint - maintained for compatibility"""
    try:
        data = request.get_json()
        question = data.get('question')
        context = data.get('context')

        if not question or not context:
            return jsonify({"error": "Missing question or context"}), 400

        # Convert to new format
        messages = [
            {"role": "system", "content": f"Answer based on this content: {context}"},
            {"role": "user", "content": question}
        ]
        
        answer = ask_llama_with_history(messages)
        return jsonify({"answer": answer})
        
    except Exception as e:
        logger.error(f"Error in legacy ask endpoint: {str(e)}")
        return jsonify({"error": "An error occurred processing your request"}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({"error": "Method not allowed"}), 405

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    # Check for required environment variables
    if not GROQ_API_KEY:
        logger.warning("GROQ_API_KEY not found in environment variables")
        print("⚠️  Warning: GROQ_API_KEY not found. Please set it in your .env file")
    else:
        logger.info("✅ GROQ_API_KEY loaded successfully")
    
    logger.info("🚀 Starting Flask application...")
    app.run(debug=True, host='127.0.0.1', port=5000)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
