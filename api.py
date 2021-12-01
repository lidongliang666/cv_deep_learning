import requests


rooturl = "http://124.70.17.227:8811/"


def getHomeworkList(createUserId):
    # 1898a796bd164dd4a2bdab56bcef4596
    url = rooturl + "zjyzwebmain/api/course/api/v1/courseHomework/getHomeworkList"
    header = {
        "token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHBpcmVzSW4iOjE3NDYyNTM1MzMsInJvbGVUeXBlSWQiOiJ0MDUwIiwibmJmIjoxNjM4MjQyNzMzLCJ1bml0SWQiOiI4ZWIxMDllZWRjODE0ODBiYjYyOTc2NzcyYjAwMmJlNiIsImNhbnRvbiI6IjExMDAwMCIsImV4cCI6MTc0NjI1MzUzMywidXNlcklkIjoiMTg5OGE3OTZiZDE2NGRkNGEyYmRhYjU2YmNlZjQ1OTYiLCJ1dWlkIjoiNzcxMWMwZjA1NzRiNDI0ZDhlMWRiNGFiNDI1OWM5ZTQiLCJpYXQiOjE2MzgyNTM1MzMsInBsYXRmb3JtIjoiZGVlNmI2ZmVmMDU0NDE1OTkzNjIwNmY3MjE1ODZiNGEifQ.9Tjj3UcvnNuV6LIVxsLJpmtLRm9NMhwcPM3i2BUXMwY",
        "Content-Type":"application/json;charset=UTF-8"
    }
    data = {"pending": 1, "createUserId":createUserId , "pageNum": 1, "pageSize": 10}
    res = requests.post(url=url,headers=header,json=data).json()
    return res