from flask import Flask, request, jsonify
from flask_cors import CORS
import ollama
import base64
import json

app = Flask(__name__)
CORS(app)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    model = data.get('model')
    messages = data.get('messages')
    image_base64 = data.get('image')

    if image_base64:
        # 将图片编码为 base64 字符串，并将其添加到消息中
        messages.append({
            'role': 'user',
            'content': '[image attached]',
            'image': image_base64
        })

    try:
        response = ollama.chat(model=model, messages=messages)
        message_content = response['message']['content']
        message_image = data.get('image')
        print(message_image)
        return jsonify({'message': {'content': message_content, 'image': message_image}})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)
