import pymysql
from timeit import default_timer
import json
host  = '112.126.120.231' 
port = 3316
db = 'zjyz-bigdata'
user = 'zjyz-dev'
password = 'Zjyz@Istop1#'

# ---- 用pymysql 操作数据库
def get_connection():
    conn = pymysql.connect(host=host, port=port, db=db,
                           user=user, password=password)
    return conn
class UsingMysql(object):

    def __init__(self, commit=False, log_time=False, log_label='总用时'):
        """

        :param commit: 是否在最后提交事务(设置为False的时候方便单元测试)
        "只查询 可以设置为False 其他更改数据库的操作需要设置为True"
        :param log_time:  是否打印程序运行总时间
        :param log_label:  自定义log的文字
        """
        self._log_time = log_time
        self._commit = commit
        self._log_label = log_label

    def __enter__(self):

        # 如果需要记录时间
        if self._log_time is True:
            self._start = default_timer()

        # 在进入的时候自动获取连接和cursor
        conn = get_connection()
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        conn.autocommit = False

        self._conn = conn
        self._cursor = cursor
        return self

    def __exit__(self, *exc_info):
        # 提交事务
        if self._commit:
            self._conn.commit()
        # 在退出的时候自动关闭连接和cursor
        self._cursor.close()
        self._conn.close()

        if self._log_time is True:
            diff = default_timer() - self._start
            print('-- %s: %.6f 秒' % (self._log_label, diff))

    @property
    def cursor(self):
        return self._cursor

def get_page_info_by_id(fileId,printId):
    sql = '''
    SELECT a.page_info,b.template_info FROM dwd_course_homework_student_newpageinfo a,dwd_course_homework_template b WHERE (a.file_id ='{}' AND b.print_id = '{}')
    '''.format(fileId,printId)
    with UsingMysql() as um:
        um.cursor.execute(sql)
        data = um.cursor.fetchone()
    return json.loads(data['page_info']),json(data['template_info'])

