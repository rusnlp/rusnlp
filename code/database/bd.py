import sqlite3
import json
from nltk.corpus import stopwords
from db_reader import ReaderDBase
from db_writer import WriterDBase


class DBaseRusNLP():
    stop_words_ru = set(stopwords.words('russian'))
    stop_words_en = set(stopwords.words('english'))
    list_of_chars = ('‘', '+', ')', ':', '2', '(', '/', '—', '…', '-', '„', '.', '1', ',', '<', '“', '«', '6', '–', '[')

    def __init__(self, db_path, config_file):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute("PRAGMA foreign_keys = OFF");
        self.cursor.execute('PRAGMA encoding = "UTF-8"')
        self.tables = json.load(open(config_file))
        for name, data in self.tables.items():
            self.create_table(name, data)
        self.author_columns = self.select_columns_name("author")
        self.article_columns = self.select_columns_name("article")
        self.catalogue_columns = self.select_columns_name("catalogue")
        self.conference_columns = self.select_columns_name("conference")

    def close(self):
        self.conn.close()

    def create_table(self, name, operations_list):
        columns_dict = operations_list[0]
        query = "CREATE TABLE IF NOT EXISTS " + name + " ("
        columns = ', '.join([key + " " + val for key, val in columns_dict.items()])
        last = ")"
        constraints = ", " + ", ".join(operations_list[1:]) if len(operations_list) > 1 else ""
        print(query + columns + last + constraints)
        self.cursor.execute(query + columns + constraints + last)
        self.conn.commit()

    def update(self, table, column, value, what, condition):
        query = '''UPDATE ''' + table
        set_col = ''' SET ''' + column + '''= ''' + self.check(value)
        where = ''' WHERE ''' + what + ''' = ''' + self.check(condition)
        try:
            self.cursor.execute(query + set_col + where)
            self.conn.commit()
        except Exception as e:
            print(query + set_col + where)

    def alter(self, table, operation, column, name, type_column):
        query = """ALTER TABLE """ + table + """ """ + operation + """ """
        col_query = column + """ """ + name + """ """ + type_column
        print(query + col_query)
        self.cursor.execute(query + col_query)
        self.conn.commit()

    def alter_add_column(self, table, name, type_col):
        self.alter(table, 'ADD', 'COLUMN', name, type_col)
        print('column ' + name + ' added')

    def delete(self, table=None, column=None, condition=None):
        query = "DELETE * FROM " + table
        where = " WHERE " + column + " = " + self.check(condition)
        self.cursor.execute(query + where)
        self.conn.commit()

    def drop(self, table):
        self.cursor.execute("DROP TABLE " + table)
        self.conn.commit()

    def select(self, what, where, condition=None):
        query = "SELECT " + what + " FROM " + where
        if condition != None:
            query += " WHERE " + condition
        print(query)
        self.cursor.execute(query)
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

    def insert(self, table, value, columns):
        query = '''INSERT INTO ''' + table
        query += ''' (''' + ''', '''.join(columns) + ''') '''
        values = ''' VALUES(''' + ''', '''.join([self.check(i) for i in value]) + '''); '''
        print(query + values)
        self.cursor.execute(query + values)
        self.conn.commit()
        print('loaded to ' + str(table))

    def check(self, value):
        if type(value) == int:
            return str(value)
        elif type(value) == str:
            value = value.replace("'", """ """).replace('"', """ """)
            value = ''.join([x for x in value if ord(x)])
            return u'' + '''"''' + value + '''"'''
        elif value == None:
            return '''NULL'''
        else:
            print(type(value))
            print(value)
            raise TypeError("Unknown type")

    def get_db_info(self):
        self.cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
        return self.cursor.fetchall()


if __name__ == 'main':
    c = DBaseRusNLP("rus_nlp_up.db", "meta_data.json")
    print(c.author_columns)
    bd_read_helper = ReaderDBase(c)
    bd_write_helper = WriterDBase(c)
    print(bd_read_helper.get_statistics())
    # print(bd_read_helper.select_author_and_title_by_id("%.+%"))
