
import json
import requests
import uuid as uuidtools


from pymysql_comme import get_examid_by_uuid_from_db

rooturl = "http://124.70.17.227:8811/"


def getHomeworkList(createUserId):
    # 1898a796bd164dd4a2bdab56bcef4596
    url = rooturl + "zjyzwebmain/api/course/api/v1/courseHomework/getHomeworkList"
    header = {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHBpcmVzSW4iOjE3NDYyNTM1MzMsInJvbGVUeXBlSWQiOiJ0MDUwIiwibmJmIjoxNjM4MjQyNzMzLCJ1bml0SWQiOiI4ZWIxMDllZWRjODE0ODBiYjYyOTc2NzcyYjAwMmJlNiIsImNhbnRvbiI6IjExMDAwMCIsImV4cCI6MTc0NjI1MzUzMywidXNlcklkIjoiMTg5OGE3OTZiZDE2NGRkNGEyYmRhYjU2YmNlZjQ1OTYiLCJ1dWlkIjoiNzcxMWMwZjA1NzRiNDI0ZDhlMWRiNGFiNDI1OWM5ZTQiLCJpYXQiOjE2MzgyNTM1MzMsInBsYXRmb3JtIjoiZGVlNmI2ZmVmMDU0NDE1OTkzNjIwNmY3MjE1ODZiNGEifQ.9Tjj3UcvnNuV6LIVxsLJpmtLRm9NMhwcPM3i2BUXMwY",
        "Content-Type": "application/json;charset=UTF-8"
    }
    data = {"pending": 1, "createUserId": createUserId,
            "pageNum": 1, "pageSize": 10}
    res = requests.post(url=url, headers=header, json=data).json()
    return res


def uploadHomeworkFile(userId, homeworkId, resourceId, imgpath):
    '''首次上传自动批阅'''
    url = rooturl + "zjyzwebmain/api/course/api/v1/courseHomeworkFile/uploadHomeworkFile"
    header = {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHBpcmVzSW4iOjE3NDY0MDcyOTUsInJvbGVUeXBlSWQiOiJ0MDUwIiwibmJmIjoxNjM4Mzk2NDk1LCJ1bml0SWQiOiI4ZWIxMDllZWRjODE0ODBiYjYyOTc2NzcyYjAwMmJlNiIsImNhbnRvbiI6IjExMDAwMCIsImV4cCI6MTc0NjQwNzI5NSwidXNlcklkIjoiMTg5OGE3OTZiZDE2NGRkNGEyYmRhYjU2YmNlZjQ1OTYiLCJ1dWlkIjoiYWFmM2M2Mzc5MzQ3NGNmMjgzOTI5M2ZmNGQ5MmEzZmMiLCJpYXQiOjE2Mzg0MDcyOTUsInBsYXRmb3JtIjoiNWZjY2RiZTZkYzkxNDE3MmEwZDgxYTAwYWJkYzhlODQifQ.S9eCKtH57f9uruJ_h7wscJ2NKAAqshiL6BhbCBd0WLU"
    }
    uploadBatch = str(uuidtools.uuid1())
    data = {
        "homeworkId": homeworkId,
        "resourceId": resourceId,
        "userId": userId,
        "uploadBatch": uploadBatch
    }

    bd = open(imgpath, 'rb')
    file = {'file': bd}
    res = requests.post(url=url, headers=header, data=data, files=file).json()
    # print(res)
    return res


def replaceHomeworkFile(homeworkId, newFileId, pageNum, resourceId, userId):
    '''重新上传'''
    url = rooturl + "zjyzwebmain/api/course/api/v1/courseHomeworkFile/replaceHomeworkFile"
    header = {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHBpcmVzSW4iOjE3NDY0MDcyOTUsInJvbGVUeXBlSWQiOiJ0MDUwIiwibmJmIjoxNjM4Mzk2NDk1LCJ1bml0SWQiOiI4ZWIxMDllZWRjODE0ODBiYjYyOTc2NzcyYjAwMmJlNiIsImNhbnRvbiI6IjExMDAwMCIsImV4cCI6MTc0NjQwNzI5NSwidXNlcklkIjoiMTg5OGE3OTZiZDE2NGRkNGEyYmRhYjU2YmNlZjQ1OTYiLCJ1dWlkIjoiYWFmM2M2Mzc5MzQ3NGNmMjgzOTI5M2ZmNGQ5MmEzZmMiLCJpYXQiOjE2Mzg0MDcyOTUsInBsYXRmb3JtIjoiNWZjY2RiZTZkYzkxNDE3MmEwZDgxYTAwYWJkYzhlODQifQ.S9eCKtH57f9uruJ_h7wscJ2NKAAqshiL6BhbCBd0WLU",
        "Content-Type": "application/json"
    }
    uploadBatch = str(uuidtools.uuid1())
    data = {
        "homeworkId": homeworkId,
        "newFileId": newFileId,
        "pageNum": pageNum,
        "resourceId": resourceId,
        "uploadBatch": uploadBatch,
        "uploadStep": 0,
        "userId": userId
    }

    # bd = open(imgpath,'rb')
    # file = {'file':bd}
    res = requests.post(url=url, headers=header, json=data).json()
    # print(res)
    return res

def uploadHomework(srcimgPath,uuid):
    '''整合首次上传  重复上传逻辑'''
    # try:
    user_id,homework_id,resource_id = get_examid_by_uuid_from_db(uuid)

    res = uploadHomeworkFile(user_id,homework_id,resource_id,srcimgPath)
    print(res)
    if res['result']:
        info = res['result'][0][-1]
        replaceHomeworkFile(homework_id,info['fileId'],info['pageNum'],resource_id,user_id)
        print("重新上传成功")
    else:
        print("首次上传成功")
    # except:
    #     print(traceback.format_exc())

# --------------------------------------------------------------------------------------------------

def uploadHomework_new(srcimgPath,print_qr_id):
    '''
        print_qr_id 是新架构学生作答页 上的二维码 内容，通过这个二维码 要查询一下内容
           userId(教师) necibook-20200823-78-admin

            isExam
            subjectId

            (调用解析用户上传图片的接口)
            "presetUserId": "4a23a12a041645269001a5c291cb3afe"
            printid 
                "fileId": "e6c212b7db38435a90b23374a7dee361",
                
                "pageNum": 1,
                "extraList": []
        1. 通过print_qr_id查 zjyz_mark_print_qr的 print_id, preset_user_id   (pymysql_comme已实现)
        2. 通过print_id 查 exam_id (pymysql_comme已实现)
        3. 通过print_id 查 zjyz_mark_exam_print 的 layout_settings 获得 extraList 知道是否包含 额外字段 (pymysql_comme已实现)
        4. exam_id 查 zjyz_mark_exam 获得 subject_id answer_method 试卷、答题纸 (pymysql_comme已实现)
        5. 调用解析用户上传图片的接口 获得 fileId,pageNum,extraList
    '''
 

def uploadHomeworkFile_new(srcimgPath):
    
    '''
        5. 调用解析用户上传图片的接口 获得 fileId,pageNum,extraList
        前端解析用户上传图片
        {
            "markPrintQrList": [
                {
                    "fileId": "a39be03693674aa9ae311dfcfd09311d",
                    "recognitionFlag": false
                }
            ],
            "userId": "necibook-20200823-78-admin"
        }
    '''
    


# {
#     "homeworkId": "c112377f9ade48a8a7e6808336c80bd3",
#     "resourceId": "e9c31bc7011547879fbcfe5ffb5fe6ee",
#     "userId": "a85b70e10b0a4501aea23ff6ca86c5a1",


#     "userName": "李虔涵",
#     "fileList": [],
#     "status": 0,
#     "studentCount": 0,
#     "pageCount": 2,
#     "examId": "bc8a8f538f1e4faab773ce7f8ff2b4f9",
#     "examName": "pyqt测试卷2"
# }
# {'id': '1228204737d8440b89a5e44e4662ed3b', 'userId': 'a85b70e10b0a4501aea23ff6ca86c5a1', 'homeworkId': 'c112377f9ade48a8a7e6808336c80bd3', 'resourceId': 'e9c31bc7011547879fbcfe5ffb5fe6ee', 'pageNum': 1, 'uploadBatch': 'fd118a49-534c-11ec-b5fd-3c7c3f8239a9',
#     'fileId': 'e23c3a5cf18547a3986aeadc0d80f0b5', 'fileName': '20211202_001.jpg', 'validFlag': '1', 'createTime': '2021-12-02 16:51:07', 'createUserId': '1898a796bd164dd4a2bdab56bcef4596', 'updateTime': '2021-12-02 16:51:07', 'updateUserId': '1898a796bd164dd4a2bdab56bcef4596', 'isNew': 1}
if __name__ == "__main__":
    # uploadHomeworkFile("a85b70e10b0a4501aea23ff6ca86c5a1","c112377f9ade48a8a7e6808336c80bd3","e9c31bc7011547879fbcfe5ffb5fe6ee","images/20211202_001.jpg")
    replaceHomeworkFile("c112377f9ade48a8a7e6808336c80bd3", "e23c3a5cf18547a3986aeadc0d80f0b5", 1,
                        "e9c31bc7011547879fbcfe5ffb5fe6ee", "a85b70e10b0a4501aea23ff6ca86c5a1")
