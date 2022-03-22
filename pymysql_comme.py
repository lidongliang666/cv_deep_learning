import json
import pymysql
from timeit import default_timer

host  = '112.126.120.231' 
port = 3316
db = 'zjyz'
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

def get_userid_by_qrid(qrid):
    sql = '''
    SELECT preset_user_id FROM zjyz_mark_print_qr WHERE id ='{}'
    '''.format(qrid)
    with UsingMysql() as um:
        um.cursor.execute(sql)
        data = um.cursor.fetchone()
    return data['preset_user_id']

def get_examid_by_uuid_from_db(uuid):
    sql = '''
    SELECT a.user_id,a.homework_id,a.resource_id FROM zjyz_course_homework_print_relate a 
    WHERE a.id = '{}'		
    '''.format(uuid)
    with UsingMysql() as um:
        um.cursor.execute(sql)
        data = um.cursor.fetchone()
    return data['user_id'],data['homework_id'],data['resource_id']


# --------------------------------新架构-------------------------------------------------

def get_printid_userid_by_printqrid(print_qr_id):
    '''通过 print_qr_id  查 printid,userid'''
    sql = '''
    SELECT a.print_id,a.preset_user_id FROM zjyz_mark_print_qr a 
    WHERE a.id = '{}'		
    '''.format(print_qr_id)
    with UsingMysql() as um:
        um.cursor.execute(sql)
        data = um.cursor.fetchone()
    if data:
        return data['print_id'],data['preset_user_id']
    else:
        return None,None

def get_examid_layoutsettings_by_printid(printid):
    sql = '''
    SELECT a.exam_id,a.layout_settings FROM zjyz_mark_exam_print a 
    WHERE a.id = '{}'		
    '''.format(printid)
    with UsingMysql() as um:
        um.cursor.execute(sql)
        data = um.cursor.fetchone()
    if data:
        return data['exam_id'], data['layout_settings'] # layout_settings 的字符串比较特殊 A4 
    else:
        return None,None

def get_subjectid_answermethod_by_examid(examid):
    sql = '''
    SELECT a.subject_id,a.answer_method FROM zjyz_mark_exam a 
    WHERE a.id = '{}'		
    '''.format(examid)
    with UsingMysql() as um:
        um.cursor.execute(sql)
        data = um.cursor.fetchone()
    if data:
        return data['subject_id'], data['answer_method'] # layout_settings 的字符串比较特殊 A4 
    else:
        return None,None


if __name__ == "__main__":
    # print(get_examid_by_uuid_from_db("0002b60f75df46a9aac30f8746d74f6e"))
    # print(get_printid_userid_by_printqrid("004078f9471c5305ebdae189c5cdbe63"))
    # print(get_examid_layoutsettings_by_printid("2bedb501fcca48fa939be17b25ce658f"))
    print(get_subjectid_answermethod_by_examid("6890c8fdbffd4272a9a7897145356fbd"))
