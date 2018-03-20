
# coding: utf-8

# In[1]:


from transliterate import translit
import sqlite3
import pickle
import sys
import re


# In[33]:


class DBaseRusNLP():
    tables = {
        "author": {
            "id": "INT PRIMARY KEY",
            "name": "text",
            "email": "text",
            "affiliation": "text"
        },

        "article": {
            "id": "INT PRIMARY KEY",
            "title": "text",
            "keywords": "text",
            "abstract": "text",
            "bibliography": "text",
            "text": "text"
        },

        'catalogue': {
            "id": "INT PRIMARY KEY",
            "author_id": "INT",
            "article_id": "INT",
            "conference_id": "INT"
        },

        'conference': {
            "id": "INT PRIMARY KEY",
            "conference": "text",
            "year": "int"
        }
    }

    def __init__(self):
        self.conn = sqlite3.connect("rus_nlp.db")
        self.cursor = self.conn.cursor()
        for name, data in self.tables.items():
            self.create_table(name, data)
        self.author_columns = self.select_columns_name("author")
        self.article_columns = self.select_columns_name("article")
        self.catalogue_columns = self.select_columns_name("catalogue")
        self.conference_columns = self.select_columns_name("conference")

    def close(self):
        self.conn.close()

    # ********************************************************************

    def create_table(self, name, columns_dict):
        query = "CREATE TABLE IF NOT EXISTS " + name + " ("
        columns = ', '.join([key + " " + val for key, val in columns_dict.items()])
        last = ")"
        self.cursor.execute(query + columns + last)
        self.conn.commit()

    # ********************************************************************

    def __update(self, table, column, value, what, condition):
        query = '''UPDATE '''+table
        set_col = ''' SET ''' + column + '''= '''+ self.__check(value)
        where = ''' WHERE ''' + what +''' = ''' + self.__check(condition)
        try:
            self.cursor.execute(query + set_col + where)
            self.conn.commit()
        except Exception as e:
            print(query + set_col + where)

    # ********************************************************************

    def delete(self, table=None, column=None, condition=None):
        pass

    # ********************************************************************

    def select(self, what, where, condition=None):
        query = "SELECT " + what + " FROM " + where
        if condition!=None:
            query += " WHERE " + condition
        self.cursor.execute(query)
        print(query)
        return self.cursor.fetchall()

    def select_max(self, table):
        query = """SELECT MAX(id) FROM """ + table + ";"
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        return rows[0][0] if rows[0][0] != None else 0
    
    def select_columns_name(self, table_name):
        query = "SELECT * FROM " + table_name
        self.cursor.execute(query)
        return [member[0] for member in self.cursor.description]

    # ********************************************************************

    def __insert(self, table, value, columns):
        query = '''INSERT INTO ''' + table
        query += ''' (''' + ''', '''.join(columns) + ''') '''
        values = ''' VALUES(''' + ''', '''.join([self.__check(i) for i in value]) + '''); '''
        self.cursor.execute(query + values)
        self.conn.commit()
        print('loaded to '+ str(table))        

    def __check(self, value):
        if type(value) == int:
            return str(value)
        elif type(value) == str:
            value = value.replace("'",""" """).replace('"', """ """).replace('\n', ' ')
            value = ''.join([x for x in value if ord(x)])
            return u''+'''"''' + value + '''"'''
        elif value == None:
            return '''NULL'''
        else:
            print(type(value))
            print(value)
            raise TypeError("Unknown type")

    # --------------------------------------------------------------------
    # --------------------------------------------------------------------

    def insert_into_conference(self, values):
        max_id = self.select_max('conference')
        for i in range(len(values)):
            row = [max_id + 1] + list(values[i])
            self.__insert('conference', row, columns=['id', 'conference', 'year'])

    # --------------------------------------------------------------------
    # --------------------------------------------------------------------

    def insert_into_author(self, id_, name, affiliation, email):
        self.__insert('author', (id_, name, email, affiliation), ["id", "name", "email", "affiliation"])

    # --------------------------------------------------------------------
    # --------------------------------------------------------------------

    def insert_into_article(self, id_, title, text, abstract, bibliography, keywords):
        self.__insert('article', (id_, title, keywords, abstract, bibliography, text), 
                     ['id', 'title', 'keywords', 'abstract', 'bibliography', 'text'])

    # --------------------------------------------------------------------
    #    INSERT NEW ARTICLE
    # --------------------------------------------------------------------

    def insert_new_article(self, author, article, conference_name, year):
        try:
            article_id = self.get_article_id(article)
        except Exception as e:
            print(e)
        author_id = self.get_author_id(author)
        conference_id = self.get_conference_id(conference_name, year)
        for auth_id in author_id:
            self.insert_to_catalogue(auth_id, article_id, conference_id)
            
    # --------------------------------------------------------------------
    # --------------------------------------------------------------------

    def get_author_id(self, author):
        list_of_authors_id = []
        for auth in author:
            author_id = self.select_id_from_author(auth['name'])
            if not author_id:
                author_id = self.select_max('author') + 1
                if type(auth['email'])!=str:
                    print(str(auth['email']) +" "+ str(type(auth['email'])))
                    raise Exception("2 emails")
                self.insert_into_author(id_=author_id, name=auth['name'], 
                                    email=auth['email'],
                                    affiliation=auth['affiliation'])
            list_of_authors_id.append(author_id)
        return list_of_authors_id

    # --------------------------------------------------------------------

    def select_id_from_author(self, name):
        where = ' name = ' + self.__check(name)
        rows = self.select(what='id', where='author', condition=where)
        return rows[0][0] if rows != [] else None

    # --------------------------------------------------------------------
    # --------------------------------------------------------------------

    def get_article_id(self, article):
        article_id = self.select_id_from_article(article['title'])
        print(article['title']+' id ='+ str(article_id))
        if not article_id:
            article_id = self.select_max('article') + 1
            if 'bibliography' not in article.keys():
                article['bibliography']=None
            else:
                print(article['bibliography'])
                raise Exception("here, bibliography")
            if 'keywords' not in article.keys():
                article['keywords']=None
            if type(article['text']==list):
                article['text']=' '.join(article['text'])
            else:
                print('wrong type')
                print(type(article['text']))
            self.insert_into_article(id_=article_id, title=article['title'], text=article['text'],
                                     abstract=article['abstract'], bibliography=article['bibliography'],
                                     keywords=article['keywords'])
        return article_id
    

    # --------------------------------------------------------------------

    def select_id_from_article(self, title):
        where = """title=""" + self.__check(title)
        rows = self.select(what='id', where='article', condition=where)
        print(rows)
        return rows[0][0] if rows != [] else None

    # --------------------------------------------------------------------
    # --------------------------------------------------------------------

    def get_conference_id(self, conference_name, year):
        conference_id = self.select_id_from_conference(conference_name, year)
        if not conference_id:
            print(conference_name+ " "+ str(year))
            raise ValueError('wrong combination of year and conference name')
        return conference_id

    def select_id_from_conference(self, conference_name, year):
        where = ''' year = ''' + str(year) + ''' AND conference = "''' + conference_name + '";'
        rows = self.select(what='id', where='conference', condition=where)
        return rows[0][0] if rows != [] else None
    
    
    # --------------------------------------------------------------------
    # --------------------------------------------------------------------
    
    def insert_to_catalogue(self, auth_id, article_id, conference_id):
        catalog_id = self.select_id_from_catalogue(auth_id, article_id, conference_id)
        if not catalog_id:
            catalog_id = self.select_max('catalogue') + 1
            self.__insert('catalogue', (int(catalog_id), int(auth_id),
                                  int(article_id), int(conference_id)), 
                          columns=['id', 'author_id', 'article_id', 'conference_id'])
    
    def select_id_from_catalogue(self, auth_id, article_id, conference_id):
        where = ''' author_id = ''' + str(auth_id) + ''' AND article_id = ''' + str(article_id) + ''' AND conference_id = ''' + str(conference_id) + ';'
        rows = self.select(what='id', where='catalogue', condition=where)
        return rows[0][0] if rows != [] else None
        

    # ********************************************************************
    
    def select_articles_of_author(self, name):
        li_name = [translit(name, 'ru'), translit(name, 'ru', reversed=True)]
        what = "DISTINCT article.title"
        where = "catalogue JOIN author JOIN article ON catalogue.author_id=author.id AND catalogue.article_id=article.id"
        condition = "author.name LIKE '%"+self.__check(li_name[0])[1:-1]+"%' OR author.name LIKE '%"+self.__check(li_name[1])[1:-1]+"%'"
        result = self.select(what, where, condition)
        return result
    
    
    def select_articles_from_conference(self, conf_name, year=None):
        what = "DISTINCT article.title"
        where = "catalogue JOIN conference JOIN article ON catalogue.conference_id=conference.id AND catalogue.article_id=article.id"
        condition = "conference.conference='"+conf_name+"'"
        if year != None:
            condition += "AND conference.year="+str(year)
        result = self.select(what, where, condition)
        return result
    
    def select_article_by_affiliation(self, affiliation):
        li_name = [self.__check(translit(affiliation, 'ru'))[1:-1], 
                   self.__check(translit(affiliation, 'ru', reversed=True))[1:-1]]
        what = "DISTINCT article.title"
        where = "catalogue JOIN author JOIN article ON catalogue.author_id=author.id AND catalogue.article_id=article.id"
        condition = "author.affiliation LIKE '%"+li_name[0]+"%' OR author.affiliation LIKE '%"+li_name[1]+"%'"
        result = self.select(what, where, condition)
        return result
    
    # ********************************************************************

    def load_to_dialog(self, dict_with_data):
        self.load('Dialog', dict_with_data)

    def load_to_aist(self, dict_with_data):
        self.load('AIST', dict_with_data)

    def load_to_ainl(self, dict_with_data):
        self.load('AINL', dict_with_data)

    def load_to_russir(self, dict_with_data):
        self.load('RuSSIR', dict_with_data)

    # --------------------------------------------------------------------

    def load(self, name, dict_with_data):
        counter = 0
        for article in dict_with_data:
            self.insert_new_article(author=article['author'], 
                                    article=article['text'],
                                    conference_name=name, 
                                    year=int(article['year']))
            counter += 1

            
    


# Подключаемся к БД:

# In[48]:


c = DBaseRusNLP()


# Добавляем (в пустую БД) конференции:

# In[49]:


try:
    for i in range(18):
        c.insert_into_conference([('Dialog',2000+i)])
    for i in range(15, 18):
        c.insert_into_conference([('AINL',2000+i)])
    for i in range(7,18):
        c.insert_into_conference([('AIST',2000+i)])
    for i in range(8,18):
        c.insert_into_conference([('RuSSIR',2000+i)])
            #c.insert_into_author()
except Exception as e:
    print(e)


# Закрываем БД:

# In[47]:


#c.close()


# Обычные запросы напрямую к БД:

# In[36]:


c.cursor.execute("""SELECT * FROM conference""")
d = c.cursor.fetchall()
print(d)


# Общая информация по БД:

# In[59]:


print(c.select_max('article'))
print(c.select_max('conference'))
print(c.select_max('author'))
print(c.select_max('catalogue'))


# Загрузка статей AINL:

# In[57]:


#with open("ainl.pickle", 'rb') as f:
#    dialog = pickle.load(f)
#    print(len(dialog), 'articles')
#    c.load_to_ainl(dialog)


# Загрузка статей Dialog:

# In[58]:


#with open("dialogue.pickle", 'rb') as f:
#    dialog = pickle.load(f)
#    print(len(dialog), 'articles')
#    c.load_to_dialog(dialog)


# Загрузка статей AIST:

# In[56]:


#with open("aist.pickle", 'rb') as f:
#    dialog = pickle.load(f)
#    print(len(dialog), 'articles')
#    c.load_to_aist(dialog)


# In[52]:


#with open("russir.pickle", 'rb') as f:
#    dialog = pickle.load(f)
#    print(len(dialog), 'articles')
#    c.load_to_russir(dialog)


# Поиск по имени (с использованием транслитерации):

# In[9]:


print(c.select_articles_of_author('Кутузов'))


# Поиск по конференции:

# In[10]:


print(c.select_articles_from_conference('Dialog', 2010))


# Поиск по аффилиации (с использованием транслитерации):

# In[105]:


print(c.select_article_by_affiliation('РАН'))


# Поле для рисеча:

# In[93]:


c.cursor.execute('SELECT affiliation FROM author')
a = c.cursor.fetchall()
print(a)


