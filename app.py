from flask import Flask, request, jsonify
from flask_cors import CORS
import ollama

app = Flask(__name__)
CORS(app)

def correct_base64_padding(base64_str):
    # 移除Base64字符串中的头部信息，如果存在
    if base64_str.startswith('data:image'):
        base64_str = base64_str.split(',', 1)[1]

    # 确保Base64字符串的长度是4的倍数
    missing_padding = len(base64_str) % 4
    if missing_padding:
        base64_str += '=' * (4 - missing_padding)
    return base64_str

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    model = data.get('model')
    messages = data.get('messages')
    image_base64 = data.get('image')
    
    # 对于传来的每条消息，如果是用户角色并且有图像数据，则添加图像
    if image_base64:
        print("Received Base64 image data")
        image_base64 = correct_base64_padding(image_base64)
        for message in messages:
            if message['role'] == 'user':
                message['images'] = [image_base64]
    else:
        # 确保无图像数据时，不添加或保留 `images` 字段
        for message in messages:
            if 'images' in message and message['images'] is None:
                del message['images']

    try:
        print("Messages sent to model:", messages)
        response = ollama.chat(model=model, messages=messages)
        message_content = response['message']['content']

        return jsonify({'message': {'content': message_content}})
    except Exception as e:
        print(f"Error during chat model processing: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)
