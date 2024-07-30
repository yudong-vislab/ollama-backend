import cv2
import os
import fitz  # fitz就是pip install PyMuPDF
import shutil
from flask import Flask, request, jsonify
from flask_cors import CORS
import layoutparser as lp
from paddleocr import PPStructure,draw_structure_result,save_structure_res

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
if __name__ == '__main__':
    app.run(port=5000)   
    
# image = cv2.imread('imgs/CLIP/images_3.img')
# image = image[..., ::-1]

# # 加载模型
# model = lp.PaddleDetectionLayoutModel(config_path="lp://PubLayNet/ppyolov2_r50vd_dcn_365e_publaynet/config",
#                                 threshold=0.5,
#                                 label_map={0: "Text", 1: "Title", 2: "List", 3:"Table", 4:"Figure"},
#                                 enforce_cpu=False ,
#                                 enable_mkldnn=True)
# # 检测
# layout = model.detect(image)

# # 显示结果
# show_img = lp.draw_box(image, layout, box_width=3, show_element_type=True)


