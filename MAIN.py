import requests
import sqlite3
from time import sleep

def GetSession():
    user_info = {
        'user_id': '',
        'password': ''
    }
    url = "http://ref.comgal.info/login_check.php"
    user_id = user_info['user_id']
    password = user_info['password']
    with requests.session() as s:
        LOGIN_INFO = {
            'user_id': user_id,
            'password': password
        }
        login_req = s.post(url, data=LOGIN_INFO)

        if login_req.status_code==200 :
            return s
        else:
            print("LOGIN_FAILED")
            return False

class Upload:
    def __init__(self,s):
        self.session = s
        self.fileDir = {}
        self.sendData = {}
        self.header = {}
        self.URL = ''

    # Upload Article
    def Article(self,subject,content, fileDir='',link1='',link2=''):
        self.Makeup_data_for_article(subject,content,self.fileDir,link1,link2)
        writeReq =  self.session.post(self.URL , headers=self.header,data=self.sendData)
        if writeReq.status_code==200 :
            print("POSTED")
            sleep(0.1)
            return writeReq.text
        else:
            print("FAILED")
            print(writeReq.status_code)
            return

    # Upload Comment
    def Comment(self,article_no,content):
        self.Makeup_data_for_comment(article_no,content)
        writeReq = self.session.post(self.URL,headers=self.header,data=self.sendData)
        if writeReq.status_code == 200:
            print("POSTED")
            return
        else:
            print("FAILED")
            print(writeReq.status_code)
            return

    #전송할 데이터 정리
    def Makeup_data_for_article(self,subject,content,fileDir='',link1='',link2=''):
        if self.fileDir :
            self.files ={
                'file1': open(self.fileDir,'rb')
            }
        else :
            self.fileDir={}
        self.sendData = {
            'subject' : str(subject),
            'memo' : content,
            'link1' : link1,
            'link2' : link2,
            'use_html' : "2"
        }
        self.header = {
            'Referer' : "http://ref.comgal.info/write.php?id=cgref",
            'Method': 'POST',
            'Content-Length': str(len(str(self.sendData)))
        }
        self.URL = "http://ref.comgal.info/write_ok.php?id=cgref"
        return

    #전송할 데이터 정리 (댓글)
    def Makeup_data_for_comment(self,article_no,content):
        self.sendData = {
            'no': str(article_no),
            'memo': content
        }
        self.header = {
            'Referer': "http://ref.comgal.info/sjzb.php?id=cgref",
            'Method': 'POST',
            'Content-Length': str(len(str(self.sendData)))
        }
        self.URL = "http://ref.comgal.info/comment_ok.php?id=cgref"
        return

class HTMLControl :
    def getHTML(self,url):
        self.req = requests.get(url)
        HTML = self.req.text
        return HTML
    # 문자열 커팅 편하게하는 함수
    def cutString(self,strS,s1,s2='',l1=1,l2=1):
        # l1,l2는 찾은 문자열로부터의 거리
        # recommend: l1 = len(str(s1))
        if not s2=='':
            index1 = strS.find(s1) + l1
            index2 = strS.find(s2) - l2
            result = strS[index1:index2]
        else :
            index1 = strS.find(s1) +l1
            result = strS[index1:]
        return result

class Parser(HTMLControl):
    def __init__(self):
        self.URL = "http://ref.comgal.info/sjzb.php?id=cgref&page="
        self.html = self.getHTML(self.URL)
        self.detect = False
        self.articles = []

    def Get_article_info(self, page):
        self.html = self.getHTML(self.URL+str(page))
        while self.html.find('cart') >=0 and not self.detect:
            # Cart value를 기준으로 나누면서 처리
            self.html = self.cutString(self.html,'cart','',2,0)
            a = self.Makeup_article_info()
            if( a =="pass"):
                continue
            else:
                article_info = a
            self.articles.append(article_info)
        return self.articles

    def Get_article_content(self, article_no):
        self.URL = "http://ref.comgal.info/sjzb.php?id=cgref&no="+str(article_no)
        self.html = self.getHTML(self.URL)
        content = self._Contents()
        return content

    def Makeup_article_info(self):
        no = self._Num()
        date = self._Date()
        title = self._Title()
        name = self._Name()
        coNum = self._coNum()
        views = self._Views()
        if len(no) <=2 :
            return "pass"
        return {'no':int(no),'title':title,'name':name,'coNum':int(coNum),'views':views,'date':date}

    # 글 내용 파싱하는 부분
    def _Date(self):
        # 글의 날짜부분만 따로 긁어옴
        h = self.cutString(self.html, 'span title', "초'>", 0, -1)
        date = self.cutString(h,"'",'초',1,-1)
        return date
    def _Num(self):
        no = self.cutString(self.html, 'color="', '</span', 15, 0)
        return no
    def _Title(self):
        self.html = self.cutString(self.html,'a href','',4,1)
        title = self.cutString(self.html,'>','</a>',1,0)
        return title
    def _coNum(self):
        self.html = self.cutString(self.html,'font style','',10,0)
        coNo = self.cutString(self.html,'>','<',2,0)
        if not coNo :
            coNo="0"
        else :
            coNo=self.cutString(coNo,'[',']',1,0)
        return coNo
    def _Name(self):
        ml = self.cutString(self.html,'hand','',4,1)
        name = self.cutString(ml,'>','span',1,2)
        return name
    def _Views(self):
        i=0
        while i<2:
            i+=1
            self.html=self.cutString(self.html,'font color','',10,0)
        views = self.cutString(self.html,'>','<',1,0)
        return views
    def _Contents(self):
        h = self.cutString(self.html, 'smartOutput', '', 10, 0)
        h = self.cutString(h, '', 'div', 0, 0)
        content = self.cutString(h,'span style','div',30,2)
        c = content.find('data/cgref')
        if c>0:
            content = content[:c] + "http://ref.comgal.info/" +content[c:]
        return content

class SQLControl:
    def __init__(self):
        db_file_name = "test.db"
        self.conn = sqlite3.connect(db_file_name)
        self.cur = self.conn.cursor()
    def CreateSQL(self):
        sql = "DROP TABLE IF EXISTS article_info"
        self.cur.execute(sql)
        self.conn.commit()

        sql = "CREATE TABLE IF NOT EXISTS article_info" \
              " (no INTEGER,title varchar(255)," \
              " name varchar(100),conum INTEGER," \
              "views INTEGER,date varchar(15)" \
              ")"
        self.cur.execute(sql)
        self.cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS article_no ON article_info (no)")
        self.conn.commit()
        #self.conn.close()
    #data 형식 (int(no),str(title),str(name),int(conum),int(views),str(date),
    def InsertQuery(self,data):
        sql = "INSERT OR IGNORE INTO article_info(no,title,name,conum,views,date) values(?,?,?,?,?,?)"
        self.cur.execute(sql,data)
        self.conn.commit()
        #self.conn.close()
    def GetQuery(self,article_no):
        sql = f"SELECT * FROM article_info WHERE no = :No"
        self.cur.execute(sql,{"No":int(article_no)})
        all_rows = self.cur.fetchall()
        for i in all_rows:
            print(i)
    def Request_many_data(self,datas):
        for data in datas:
            converted_data = Convert_Data_to_SQLData(data)
            self.InsertQuery(converted_data)

def Convert_Data_to_SQLData(_data):
    print(_data)
    tuple = (_data['no'],_data['title'],_data['name'],_data['coNum'],_data['views'],_data['date'])
    print(tuple)
    return tuple

SQL = SQLControl()
SQL.CreateSQL()
session = GetSession()
uploader = Upload(session)
parser = Parser()
while True:
    a = parser.Get_article_info(1)
    SQL.Request_many_data(a)

    sleep(1)

no = input("글번호를 입력해주세요")
SQL.GetQuery(no)
#c = parser.Get_article_content()
#uploader.Article('Test',c)


