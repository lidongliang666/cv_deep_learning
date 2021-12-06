from pyzbar import pyzbar

"zbar 二维码检测"

def decode_by_pyzbar(img,symbols=[pyzbar.ZBarSymbol.QRCODE]):
    """ Detect QR code and barcode in the image.
    @param img (numpy.ndarray): the image to be processed.
    @return (list): a list containing all the features detected.
    """
    QR_dict={}
    # Find barcodes and QR codes
    objects = pyzbar.decode(img, symbols=symbols)
    for obj in objects:
        (x, y, w, h) = obj.rect
        data = obj.data.decode('utf-8')
        QR_dict[(x,y,w,h)] = data
 
    return QR_dict


if __name__ == "__main__":
    import cv2
    imgpath = 'barcode/1.jpg'
    img = cv2.imread(imgpath)
    print(img,'*********')
    print(decode_by_pyzbar(img,symbols=None))