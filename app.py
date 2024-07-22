from flask import Flask, request, jsonify
from flask_cors import CORS
import ollama
import base64
import os
from PIL import Image
from io import BytesIO

app = Flask(__name__)
CORS(app)

def correct_base64_padding(base64_str):
    # 确保Base64字符串的长度是4的倍数
    missing_padding = len(base64_str) % 4
    if missing_padding:
        base64_str += '=' * (4 - missing_padding)
    return base64_str

def save_base64_image(base64_str, output_path):
    try:
        # 打印 Base64 字符串的前 100 个字符以供调试
        print(f"Base64 string (first 100 chars): {base64_str[:100]}")
        
        # 移除Base64字符串中的头部信息
        if base64_str.startswith('data:image'):
            base64_str = base64_str.split(',', 1)[1]
        
        # 打印移除头部信息后的 Base64 字符串的前 100 个字符以供调试
        print(f"Base64 string without header (first 100 chars): {base64_str[:100]}")
        
        base64_str = correct_base64_padding(base64_str)
        
        # 打印添加填充后的 Base64 字符串的前 100 个字符以供调试
        print(f"Base64 string with padding (first 100 chars): {base64_str[:100]}")
        
        image_data = base64.b64decode(base64_str)
        
        # 打印解码后的图像数据的前 100 个字节以供调试
        print(f"Image data (first 100 bytes): {image_data[:100]}")
        
        image = Image.open(BytesIO(image_data))
        
        # 打印图像信息以供调试
        print(f"Image format: {image.format}, size: {image.size}, mode: {image.mode}")
        
        image.save(output_path)
        return output_path
    except Exception as e:
        print(f"Error saving image: {e}")
        return None

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    model = data.get('model')
    messages = data.get('messages')
    image_base64 = data.get('image')
    
    image_path = None
    if image_base64:
        print("Received Base64 image data")
        # 将 Base64 字符串保存为当前工作目录中的图片文件
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, 'uploaded_image.png')
        image_path = save_base64_image(image_base64, image_path)
        if image_path:
            # 查找包含图像的消息并添加图像路径和内容
            for message in messages:
                if message.get('hasImage'):
                    message['content'] = f"{image_path} {message['content']}"
                    break

    try:
        print("Messages sent to model:", messages)  # 打印传递给模型的消息
        response = ollama.chat(model=model, messages=messages)
        message_content = response['message']['content']

        # 删除保存的图像文件
        if image_path and os.path.exists(image_path):
            os.remove(image_path)

        return jsonify({'message': {'content': message_content, 'image': image_base64}})
    except Exception as e:
        print(f"Error during chat model processing: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)
