from tempfile import TemporaryDirectory
import os

from .QR_detect_by_pyzbar import decode_by_pyzbar
from .QR_detect_by_default import detecte,find_QR_position
import cv2
import numpy as np
import zxing

"综合的二维码检测"

def QR_detect(image):
    '''
    QRpyzbar_dict：pyzbar包检测出的二维码，是一个字典，key：二维码的位置信息，value：二维码中存储的内容
    QRpyzbar_dict_order_keys：是由QRpyzbar_dict中的key组成的一个列表，按照从上到下的位置排序
    QRdefault_position：用传统方法获取到的二维码的位置信息
    '''
    # 对image做开，闭运算，提高二维码的检测识别率
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _,gray = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU + cv2.THRESH_BINARY)
    img_Guassian = cv2.GaussianBlur(gray, (1,1), 0)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (1, 1))
    img_open = cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel)
    img_open_close = cv2.morphologyEx(img_open, cv2.MORPH_CLOSE, kernel)
    # 先使用pyzbar获取能检测到的二维码区域
    QRpyzbar_dict = decode_by_pyzbar(img_open_close)
    QRpyzbar_dict_order = dict(sorted(QRpyzbar_dict.items(), key=lambda x:x[0][1], reverse=False))
    QRpyzbar_dict_order_keys = list(QRpyzbar_dict_order.keys())
    #在使用传统图像处理方式检测二维码区域
    image_contours, contours, hierachy = detecte(image)
    QRdefault_position = find_QR_position(image_contours, contours, np.squeeze(hierachy))
    QRdefault_position.sort(key=lambda x:x[1])
    # print("QRpyzbar_dict_order",QRpyzbar_dict_order)
    # 将传统方式与pyzbar方式相结合，返回最终结果
    while QRdefault_position and QRpyzbar_dict_order_keys:          
    # 删除QRdefault_position和QRpyzbar_dict_order_keys中共同出现的元素
        temp = QRdefault_position[0]
        for each in QRpyzbar_dict_order_keys:
            if abs(temp[0] - each[0]) + abs(temp[1] - each[1]) < 15:
                QRdefault_position.remove(temp)
                QRpyzbar_dict_order_keys.remove(each)
                break
        # 当二维码的位置信息不在QRpyzbar_dict_order_keys中时，用pyzbar包解析该位置的内容
        if temp in QRdefault_position:
            top = temp[1] - 10
            bottom = temp[1] + temp[3] + 10
            left = temp[0] - 10
            right = temp[0] + temp[2] + 10
            # 用zxing包解析该位置的内容
            data = QR_detect_by_zxing(image[top:bottom, left:right])
            # objects = pyzbar.decode(image[top:bottom, left:right], symbols=[pyzbar.ZBarSymbol.QRCODE])
            # 将解析出的内容添加到最终结果中
            # for obj in objects:
            #     data = obj.data.decode('utf-8')
            #     QRpyzbar_dict_order[tuple(temp)] = data
            if  data:
                QRpyzbar_dict_order[tuple(temp)] = data
            QRdefault_position.remove(temp)
    # 只剩下QRdefault_position中有二维码的位置信息时
    while QRdefault_position:
        for each in QRdefault_position:
            # print("each:",each)
            top = each[1] - 5
            bottom = each[1] + each[3] + 5
            left = each[0] - 5
            right = each[0] + each[2] + 5
            # 用zxing包解析该位置的内容
            data = QR_detect_by_zxing(image[top:bottom, left:right])
            # objects = pyzbar.decode(image[top:bottom, left:right], symbols=[pyzbar.ZBarSymbol.QRCODE])
            # 将解析出的内容添加到最终结果中
            # for obj in objects:
            #     data = obj.data.decode('utf-8')
            #     QRpyzbar_dict_order[tuple(temp)] = data
            if data:
                QRpyzbar_dict_order[tuple(each)] = data
            QRdefault_position.remove(each)
    return QRpyzbar_dict_order

def QR_detect_by_zxing(img_cut):
    try:
        #找个临时地方存储一下图片
        # 上下文 自动删除文件夹
        with TemporaryDirectory() as dirname:
            outpath = os.path.join(dirname,'temp.jpg')
            cv2.imwrite(outpath,img_cut)
            reader = zxing.BarCodeReader()
            barcode = reader.decode(outpath)
            if barcode:
                return barcode.parsed
            else:
                return None
    except:
        return None

if __name__ == "__main__":
    img = cv2.imread("camera/8.jpg")
    r = QR_detect(img)
    print(r)