from flask import Flask, request, jsonify
from flask_cors import CORS
import ollama
import fitz  # fitz就是pip install PyMuPDF
import shutil
import cv2
import os
import layoutparser as lp
from paddleocr import PPStructure,draw_structure_result,save_structure_res

app = Flask(__name__)
CORS(app)
app = Flask(__name__)
CORS(app)

def pyMuPDF_fitz(pdfPath, imagePath):#pdf转图片
    # print("imagePath=" + imagePath)
    pdfDoc = fitz.open(pdfPath)
    for pg in range(pdfDoc.page_count):
        page = pdfDoc[pg]
        rotate = int(0)
        # 每个尺寸的缩放系数为4，这将为我们生成分辨率提高4的图像。
        # 此处若是不做设置，默认图片大小为：792X612, dpi=96
        zoom_x = 4  # (1.33333333-->1056x816)   (2-->1584x1224)
        zoom_y = 4
        mat = fitz.Matrix(zoom_x, zoom_y).prerotate(rotate)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        if not os.path.exists(imagePath):  # 判断存放图片的文件夹是否存在
            os.makedirs(imagePath)  # 若图片文件夹不存在就创建

        pix._writeIMG(imagePath + '/' + 'images_%s.img' % pg,1,'img')  # 将图片写入指定的文件夹内
def correct_base64_padding(base64_str):
    # 移除Base64字符串中的头部信息，如果存在
    if base64_str.startswith('data:image'):
        base64_str = base64_str.split(',', 1)[1]

    # 确保Base64字符串的长度是4的倍数
    missing_padding = len(base64_str) % 4
    if missing_padding:
        base64_str += '=' * (4 - missing_padding)
    return base64_str
@app.route('/parse', methods=['POST'])
def parsepdf():
    data = request.json
    fileurl = data.get('url')
    parsered=False
    print(fileurl)
    rescontent=os.path.join('imgs',fileurl[:-4])
    print(os.path.join('imgs',fileurl[:-4]))
    if not os.path.exists(rescontent):
        pyMuPDF_fitz(fileurl,rescontent)      
        table_engine = PPStructure(show_log=True)
        save_folder = './result'
        fi_d=os.path.join('imgs',fileurl[:-4])
        for img in os.listdir(fi_d):
            img_path = os.path.join(fi_d,img)
            img = cv2.imread(img_path)
            result = table_engine(img)
            # 保存在每张图片对应的子目录下
            save_structure_res(result, os.path.join(save_folder,fileurl[:-4]),os.path.basename(img_path).split('.')[0])
        parsered = True
    else:
        parsered=True
    return jsonify({'res': parsered,'where':rescontent})
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
        prompt = "For the content:" + message_content + ", use three key words in English academic style to describe the main idea."
        resp = ollama.generate(model=model,prompt=prompt)
        print(resp)
        conclude = resp['response']
        return jsonify({'message': {'content': message_content,'conclude':conclude}})
    except Exception as e:
        print(f"Error during chat model processing: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)
