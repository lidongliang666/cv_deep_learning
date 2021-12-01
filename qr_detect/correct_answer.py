from PIL.Image import NONE
import cv2
import numpy as np

from .util import PageNoDecoder
from .QR_detect import QR_detect

class AnswercardCorrect:
    s_w = 1242 #模板宽
    s_h = 1756 
    s_s = 1087 #模板矫正框面积
    s_point_config = {
        "A3":{
            'tl':[49, 49],
            'tr':[2435,   49],
            'bl':[  49, 1707],
            'br':[2435,1707]
        },
        "A4":{
            'tl':[52, 50],
            'tr':[1192,   52],
            'bl':[  52, 1702],
            'br':[1192,1702]
        }
    }
    s_size = (1242, 1756)# 模板的w,h
    filter_threshold = 0.2  # 值越小，要求矩形更加标准 一般不超过0.1
    pageNoDecoder = PageNoDecoder()
    def predict(self,imgpath,paperType="A4"):
        if isinstance(imgpath,np.ndarray):
            img=imgpath
        else:
            img = cv2.imread(imgpath)
        
        if img is None:
            return "","",""
        correct_img= self.correct(img,paperType)
        # cv2.imshow("co",correct_img)
        # cv2.waitKey(0)
        if isinstance(correct_img,str):
            return "","",""
        try:
            qr_dict = QR_detect(correct_img)
            if not len(qr_dict):
                qr_dict = QR_detect(img)
        except:
            # 对于某些图片，之前同事写的代码会报错（这个图片zbar也检测不到）
            # 修改一下这里的逻辑，虽然二维码检测不到，倒是还是要 矫正后的图片返回，其他流程会用到
            return correct_img,'',''

        cut_h = int(correct_img.shape[0] / 20) # 我们截取校正后图片h的 1/20 部分来做页码解析
        cut_w = int(correct_img.shape[1] / 10) # 我们截取校正后图片w的1/10 部分来做页码解析
        # cv2.imwrite("answer_cut2.jpg",correct_img[:cut_h,cut_w:-cut_w,:])
        page_no = self.pageNoDecoder(correct_img[:cut_h,cut_w:-cut_w,:])
        return correct_img,qr_dict,page_no


    def get_contours_box(self,imgpath):
        """
        return blank_block_list -> [[c_s, centre]]；c_s轮廓面积 centre 轮廓中心点，
        这里的轮廓包含了矫正、页码解析、二维码三角（干扰）这三部分的轮廓
        """
        if isinstance(imgpath,str):
            img = cv2.imread(imgpath)
        elif isinstance(imgpath, np.ndarray):
            img = imgpath
        else:
            raise "TypeError:param imgpath must be str or np.array"
        # 通过宽的比例计算，模板在此宽度下 理论矫正轮廓面积是多少
        # 用户上传图片，一定会引入背景，所以理论模板矫正轮廓面积是用户图矫正面积的最大值。
        self.img_w = min(img.shape[:2])
        
        s_max = (self.img_w/self.s_w)*(self.img_w/self.s_w) * self.s_s
        # 考虑引入背景的情况，假设背景占宽度1/3，那么对应面积为 s_max* 4/9
                                                                                                                                                                 
        s_min = s_max * (4/9) * (4/9)

        contours = self.getContours(img)
        # contours =  self.getContours_edged(img)
        blank_block_list = []
        for i in contours:
            s = cv2.contourArea(i)
            if s_min < s <= s_max:
                # cv2.drawContours(img, [i], -1, (0, 0, 255), 3)
                # cv2.putText(img, str(s), tuple(
                #     i[-1][0]), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 2)

                cnt = cv2.minAreaRect(i)
                box = cv2.boxPoints(cnt)
                c_s = cv2.contourArea(i)
                # 将人为矩形框过滤掉
                if self.contour_si_filted(box,c_s,img):
                    continue
                # 计算轮廓中心
                contours_np = np.array(box)
                centre = np.mean(contours_np, axis=0).squeeze()
                centre = np.around([centre]).astype(np.int16).squeeze()
                blank_block_list.append([sum(img[centre[1],centre[0]]),centre])
        #         cv2.drawContours(img, [i], -1, (0, 0, 255), 3)
        #         cv2.circle(img, tuple(centre), 1, (255, 255, 255), 5)
        # cv2.imwrite("Wild1_v.jpg",img)
        return blank_block_list

    def correct(self,img,paperType):
        blank_block_list = self.get_contours_box(img)
        out_size = (AnswercardCorrect.s_w,AnswercardCorrect.s_h) if paperType == 'A4' else (AnswercardCorrect.s_w*2,AnswercardCorrect.s_h)
        if len(blank_block_list) < 3:
            print(f"矫正失败,检测到的矫正圆个数为{len(blank_block_list)},我们至少需要三个")
            print(blank_block_list)
            return ""
        else:
            # blank_block_list.sort(key=lambda item: item[0], reverse=True)
            # print(blank_block_list)
            keypoint_dict = self.get_keypoints(blank_block_list,paperType)
            src_list = []
            tar_list = []
            for k in keypoint_dict:
                src_list.append(keypoint_dict[k]) 
                tar_list.append(self.s_point_config[paperType][k])
            if len(keypoint_dict) == 4:
                mat = cv2.getPerspectiveTransform(np.float32(src_list), np.float32(tar_list))
                # print(np.float32(src_list))
                # print(np.float32(tar_list))
                correct_img = cv2.warpPerspective(img, mat,out_size ,borderValue=(255,255,255))
            else:
                mat = cv2.getAffineTransform(np.float32(src_list), np.float32(tar_list))
                correct_img = cv2.warpAffine(img, mat, out_size,borderValue=(255,255,255))
            return correct_img
    def get_keypoints(self,blank_block_list,paperType):
        if len(blank_block_list) == 3:
            raise "检测到三个矫正点，处理这种情况的代码未编写"
        else:
            #计算一下 两点之间的距离，获得两个最大的距离
            res_dict = {}
            dis_list = []
            dis_dict = {}
            # print(blank_block_list)
            for i in range(len(blank_block_list)):
                for j in range(i+1,len(blank_block_list)):
                    dis = np.linalg.norm(blank_block_list[i][1] - blank_block_list[j][1])
                    dis_list.append([dis,(i,j)])
                    dis_dict[(i,j)] = dis
                    dis_dict[(j,i)] =dis
            dis_list.sort(key=lambda itme:itme[0],reverse=True)
            # print(dis_list)
            where_is_br = -1
            where_is_tl = -1
            # print(dis_list)
            for i,info  in enumerate(dis_list):
                _,ij = info
                if blank_block_list[ij[0]][0] > 255*3/2 :
                    res_dict["br"] = blank_block_list[ij[0]][1]
                    res_dict["tl"] = blank_block_list[ij[1]][1]
                    where_is_br = ij[0]
                    where_is_tl = ij[1]
                    break
                if blank_block_list[ij[1]][0] > 255*3/2 :
                    res_dict["br"] = blank_block_list[ij[1]][1]
                    res_dict["tl"] = blank_block_list[ij[0]][1]
                    where_is_br = ij[1]
                    where_is_tl = ij[0]
                    break
            # print(where_is_br,where_is_tl,"----------")
            if len(res_dict) == 0:
                raise "右下角矫正边框丢失"
            
            else:
                other_point =[]
                for _, ij in dis_list:
                    i,j = ij
                    if len(other_point)> 1:
                        break
                    if not i in [where_is_br,where_is_tl]+other_point:
                        for n in [where_is_br,where_is_tl] + other_point:
                            if dis_dict[(i,n)] < self.img_w /4:
                                break
                        else:
                            other_point.append(i)
                    if not j in [where_is_br,where_is_tl] + other_point:
                        for n in [where_is_br,where_is_tl] + other_point:
                            if dis_dict[(j,n)] < self.img_w/4:
                                break
                        else:
                            other_point.append(j) 
                if len(other_point) <= 1:
                        raise "透视变化找不到第三，第四个点"
                # print(other_point)
                point1 = blank_block_list[other_point[0]][1]
                point2 = blank_block_list[other_point[1]][1]
                # print(point1,point2)
                d1 = np.linalg.norm(point1 - res_dict['br'])
                d2 = np.linalg.norm(point2 - res_dict['br'])
                if d1>d2:
                    res_dict['tr'] = point1
                    res_dict['bl'] = point2
                else:
                    res_dict['tr'] = point2
                    res_dict['bl'] = point1
                #如果纸张类型是A3 那么需要调换一下 左下 和 右上的位置
                if paperType == "A3":
                    temp = res_dict['bl']
                    res_dict['bl'] = res_dict['tr']
                    res_dict['tr'] = temp
            # print(res_dict)
            return res_dict
            
    def getContours(self,img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(
            binary, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        return contours
    
    def contour_si_filted(self,box,c_s,img=None):
        box_s = cv2.contourArea(box)
        return (box_s - c_s) / c_s > self.filter_threshold

class ExercisebookCorrect:

    def load_image(self,imgpath):
        img = cv2.imread(imgpath)
        # Convert image to gray and blur it
        src_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        src_gray = cv2.blur(src_gray, (3,3))
    

if __name__ == "__main__":
    answercardCorrect = AnswercardCorrect()
    # answercardCorrect = AnswercardWildCorrect()
    correct_img,qr_dict,page_no = answercardCorrect.predict("camera/8.jpg")
    cv2.imwrite(r"camera/8_correct.jpg",correct_img)
    print(qr_dict)
    print(page_no)
    # print(qr_dict)


    # img = cv2.imread(r"answer_cut2.jpg")
    # page_no = answercardCorrect.decode_page_no(img)
    # print(f"页码：{page_no}")
 