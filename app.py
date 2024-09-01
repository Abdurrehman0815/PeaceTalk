from flask import Flask, request, jsonify, send_from_directory
import google.generativeai as genai
from twilio.rest import Client
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

# Twilio credentials from environment variables
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_NUMBER")
doctor_number = os.getenv("DOCTOR_NUMBER")

# Initialize Twilio client
client = Client(account_sid, auth_token)

# Define abnormal words
abnormal_words = [
    "killing", "die", "suicide", "self-harm", "self-injury", "overdose", "harm", 
    "depression","end my life", "take my life", "commit suicide", 
    "poison", "cut", "murder", "assault", "danger", "dangerous", "death", "die by", "end it all", 
    "end it", "not worth living", "worthless"
]

def trigger_call(user_id):
    try:
        call_message = f"Alert: User ID {user_id} has mentioned concerning words in their chat. Please check on them immediately."
        twiml_response = f'<Response><Say>{call_message}</Say><Pause length="1"/><Say>{call_message}</Say></Response>'
        
        # Create the call
        call = client.calls.create(
            twiml=twiml_response,
            to=doctor_number,
            from_=twilio_number
        )
        print(f"Call triggered to doctor: {call.sid}")
    except Exception as e:
        print(f"Failed to trigger call: {e}")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_input = request.json.get("message")
        user_id = request.json.get("user_id")

        if user_input is None or user_id is None:
            return jsonify({"error": "Invalid request"}), 400

        print(f"Received user input: {user_input} from user_id: {user_id}")

        # Check for abnormal words in user input
        if any(word in user_input.lower() for word in abnormal_words):
            print(f"Abnormal word detected. Triggering call for user_id: {user_id}")
            trigger_call(user_id)

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
    return send_from_directory('static', 'index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

