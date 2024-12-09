from flask import Flask, request, jsonify
import json
import requests
from google.oauth2 import service_account
import google.auth.transport.requests

# Cấu hình tệp service account và project ID
import os


SERVICE_ACCOUNT_FILE = "chat.json"
PROJECT_ID = "chat-location-4be1f"

app = Flask(__name__)

# Hàm lấy Access Token từ Firebase
def get_access_token():
    chat_json_content = os.getenv("CHAT_JSON")
    if chat_json_content:
        with open("chat.json", "w") as f:
            f.write(chat_json_content)
    else:
        raise ValueError("CHAT_JSON environment variable is not set")
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=["https://www.googleapis.com/auth/firebase.messaging"]
    )
    request = google.auth.transport.requests.Request()
    credentials.refresh(request)
    return credentials.token

# Hàm gửi thông báo qua Firebase
def send_notification(device_token, title, body, data=None):
    url = f"https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send"
    
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json; UTF-8",
    }

    # Payload gửi thông báo
    payload = {
        "message": {
            "token": device_token,
            "notification": {
                "title": title,
                "body": body
            },
            "data": data if data else {}
        }
    }

    # Gửi request POST
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return {"status": "success", "response": response.json()}
    else:
        return {"status": "failed", "error": response.text}

# API endpoint để gửi thông báo
@app.route('/send-notification', methods=['POST'])
def handle_notification():
    try:
        # Nhận JSON từ yêu cầu
        data = request.get_json()
        device_token = data.get("device_token")
        title = data.get("title", "Notification")
        body = data.get("body", "You have a new message!")
        extra_data = data.get("data", {})

        if not device_token:
            return jsonify({"error": "Device token is required"}), 400

        # Gửi thông báo
        result = send_notification(device_token, title, body, extra_data)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
