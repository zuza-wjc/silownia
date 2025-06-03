import jwt as jwt
import requests as requests
from flask import Flask, request, jsonify

app = Flask(__name__)


SECRET_KEY = "supersecret"
MICROSERVICE_URL = 'http://kong:8000/user-service/membership'


@app.route('/')
def get_pass():
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return jsonify({"error": "Brak tokenu w nagłówku"}), 401

    if auth_header.startswith("Bearer "):
        token = auth_header[len("Bearer "):]
    else:
        return jsonify({"error": "Token nie jest w formacie Bearer"}), 401

    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        username = decoded_token.get('name')
        user_id = decoded_token.get('sub')
        email = decoded_token.get('email')

        response = jsonify({"message": 'App pass-service success'})
        response.headers["X-Username"] = username or ""
        response.headers["X-User-Id"] = user_id or ""
        response.headers["X-Email"] = email or ""

        return response
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token wygasł"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Token jest nieprawidłowy"}), 401


@app.route('/membership', methods=['POST'])
def post_pass():
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        return jsonify({"error": "Brak tokenu w nagłówku"}), 401

    if auth_header.startswith("Bearer "):
        token = auth_header[len("Bearer "):]
    else:
        return jsonify({"error": "Token nie jest w formacie Bearer"}), 401

    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        data = request.get_json()
        payment_method = data.get('payment_method')
        type = data.get('type')
        email = decoded_token.get('email')

        print(payment_method)
        print(type)

        data = {
            'email': email,
            'payment_method': payment_method,
            'type': type
        }

        try:
            response = requests.post(MICROSERVICE_URL, json=data, timeout=5000)
            response.raise_for_status()
        except requests.RequestException as e:
            return jsonify({"error": str(e)}), 502

        return jsonify({"status": "sent", "microservice_response": response.json()})

    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Token wygasł"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Token jest nieprawidłowy"}), 401


@app.route('/passes')
def get_all_passes():
    return 'Return all passes from pass-service'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
