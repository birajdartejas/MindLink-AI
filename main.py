from flask import Flask, render_template, jsonify, request
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import os
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Flask app setup
app = Flask(__name__)

# MongoDB configuration
app.config["MONGO_URI"] = os.getenv('MONGO_URI')
mongo = PyMongo(app)

# Configure Gemini SDK
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

@app.route("/")
def home():
    """Render the homepage with stored chat history."""
    chats = mongo.db.chats.find({})
    myChats = [chat for chat in chats]
    return render_template("index.html", myChats=myChats)

@app.route("/api", methods=["GET", "POST"])
def qa():
    """Handle question and answer functionality."""
    if request.method == "POST":
        question = request.json.get("question")
        if not question:
            return jsonify({"error": "Question not provided"}), 400
        
        # Check if the question already exists in the database
        chat = mongo.db.chats.find_one({"question": question})
        if chat:
            return jsonify({"question": question, "answer": chat['answer']})
        
        # Generate response using Gemini SDK
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            # Use Gemini's generative model to generate a response
            response = model.generate_content(question)
            
            # Extract the generated answer
            answer = response.text
            
            # Save to MongoDB and return the result
            mongo.db.chats.insert_one({"question": question, "answer": answer})
            return jsonify({"question": question, "answer": answer})
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return jsonify({"error": "Failed to fetch response from Gemini API."}), 500

    # Default response for GET requests
    return jsonify({"result": "Welcome to the Q&A API!"})

if __name__ == "__main__":
    app.run(debug=True, port=5001)
