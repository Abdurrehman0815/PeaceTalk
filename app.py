from flask import Flask, request, jsonify, send_from_directory
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure the Gemini API
genai.configure(api_key=os.getenv("GENAI_API_KEY"))

# Define the generation parameters
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

# Create the model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
    system_instruction="You need to act as a mental health doctor and ask questions to classify the patient to which type of mental health disorder they are having. Use this website for reference: https://www.betterhealth.vic.gov.au/health/servicesandsupport/types-of-mental-health-issues-and-illnesses. Ask only a few questions and reply in a manner that can make them feel better. Text in a friendly manner. Make all the conclusions in an ethical and moral way. Don't try to start violence, make them realize peace is the perfect thing to solve any problem.",
)

# Initialize chat session
chat_session = model.start_chat(history=[])

@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_input = request.json.get("message")

        if user_input is None:
            return jsonify({"error": "Invalid request"}), 400

        print(f"Received user input: {user_input}")

        # Generate the response from the model
        response = chat_session.send_message(user_input)
        model_response = response.text

        print(f"Model response: {model_response}")

        return jsonify({"response": model_response})

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route("/")
def index():
    return send_from_directory('templates', 'index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
