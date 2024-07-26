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

# @app.route('/api/generate',methods=['POST'])
# def generate():
#     data=request.json
#     model=data.get('model')
#     prompt=data.get('prompt')
#     print(prompt)
#     try:
#         response = ollama.generate(model=model,prompt=prompt)
#         message_content = response['response']
#         print(message_content)
#         return jsonify({'conclude':message_content})
#     except Exception as e:
#         print(f"Error during chat model processing: {e}")
#         return jsonify({'error': str(e)}), 500    
@app.route('/api/chat', methods=['POST'])
def chat():
    concludeflag = 0
    data = request.json
    model = data.get('model')
    messages = data.get('messages')
    image_base64 = data.get('image')
    # 对于传来的每条消息，如果是用户角色并且有图像数据，则添加图像
    if image_base64:
        concludeflag=1
        print("Received Base64 image data")
        image_base64 = correct_base64_padding(image_base64)
        for message in messages:
            if message['role'] == 'user':
                message['images'] = [image_base64]
    else:
        # 检查并移除不符合格式的图像数据
        for message in messages:
            if 'images' in message:
                if isinstance(message['images'], list) and message['images']:
                    # 格式化所有图像数据
                    message['images'] = [correct_base64_padding(image) for image in message['images'] if image.startswith('data:image')]
                else:
                    # 如果没有图像或者图像字段为空，移除该字段
                    del message['images']
    try:
        print("Messages sent to model:", messages)
        response = ollama.chat(model=model, messages=messages)
        message_content = response['message']['content']
        conclude = ''
        prompt = "我将给你提供一段内容，这段内容是对一张图片的描述。请你用一两个词来总结这段文字，能够实现对这张未知图片的描述和标记。图片的文字描述如下："+message_content
        resp = ollama.generate(model=model,prompt=prompt)
        print(resp)
        conclude = resp['response']
        return jsonify({'message': {'content': message_content,'conclude':conclude}})
    except Exception as e:
        print(f"Error during chat model processing: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)
