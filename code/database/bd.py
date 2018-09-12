import sqlite3
import json
from db_reader import ReaderDBase
from db_writer import WriterDBase


class DBaseRusNLP:
    def __init__(self, db_path, config_file):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
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
        """

        :param name:
        :param operations_list:
        :return:
        """
        columns_dict = operations_list[0]
        query = "CREATE TABLE IF NOT EXISTS " + name + " ("
        columns = ', '.join([key + " " + val for key, val in columns_dict.items()])
        last = ")"
        constraints = ", "+", ".join(operations_list[1:]) if len(operations_list) > 1 else ""
        # TODO: Replace prints with logging
        # print(query + columns + last+constraints)
        self.cursor.execute(query + columns + constraints+last)
        self.conn.commit()

    def update(self, table, column, value, what, condition):
        """

        :param table:
        :param column:
        :param value:
        :param what:
        :param condition:
        :return:
        """
        query = '''UPDATE {}'''.format(table)
        set_col = ''' SET ''' + column + '''= '''+ self.check(value)
        where = ''' WHERE ''' + what + ''' = ''' + self.check(condition)
        try:
            self.cursor.execute(query + set_col + where)
            self.conn.commit()
        except Exception as e:
            pass
            # TODO: Replace prints with logging
            print(query + set_col + where)
    
    def alter(self, table, operation, column, name, type_column):
        """

        :param table:
        :param operation:
        :param column:
        :param name:
        :param type_column:
        :return:
        """
        query = """ALTER TABLE """ + table + """ """ + operation + """ """
        col_query = column + """ """ + name + """ """ + type_column
        # TODO: Replace prints with logging
        print(query+col_query)
        self.cursor.execute(query + col_query)
        self.conn.commit()
    
    def alter_add_column(self, table, name, type_col):
        """
        Add column to the right

        :param table:
        :param name:
        :param type_col:
        :return:
        """
        self.alter(table, 'ADD', 'COLUMN', name, type_col)
        # TODO: Replace prints with logging
        print('column ' + name + ' added')

    def delete(self, table=None, column=None, condition=None):
        """
        Delete a single value from the table

        :param table: string
            The name of the table
        :param column: string
            The name of the column
        :param condition: list of strings
            The optional condition
        :return:
        """
        query = "DELETE FROM " + table
        where = " WHERE {} = {}".format(column, self.check(condition))
        self.cursor.execute(query + where)
        self.conn.isolation_level = None
        self.cursor.execute('VACUUM')
        self.conn.isolation_level = ''
        self.conn.commit()

    def drop(self, table):
        """
        Remove table

        :param table: string
            The name of the table
        :return: None
        """
        self.cursor.execute("DROP TABLE {}".format(table))
        self.conn.commit()

    def select(self, what, where, condition=None):
        """
        Get rows by query

        :param what: list of strings
            Columns from which the values should be selected
        :param where: string
            The name of the specified table
        :param condition: list of strings
            The optional condition according to which the rows would be selected
        :return:
        """
        query = '''SELECT {} FROM {}'''.format(what, where)
        if condition:
            query += ''' WHERE {}'''.format(condition)
        # TODO: Replace prints with logging
        #print(query)
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def select_max(self, table):
        """
        Get maximum value in the row

        :param table: string
            The name of the specified table
        :return: int
            The maximum value
        """
        query = """SELECT MAX(id) FROM """ + table + ";"
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        if rows[0][0]:
            return rows[0][0]
        return 0
    
    def select_columns_name(self, table_name):
        """
        Get names of the columns in the table

        :param table_name: string
            The name of the specified table
        :return: list of strings
            Names of the columns
        """
        query = "SELECT * FROM " + table_name
        self.cursor.execute(query)
        return [member[0] for member in self.cursor.description]

    def insert(self, table, value, columns):
        """
        Inserts a value to the table

        :param table: list of strings
            The table
        :param value: string
            The specified value
        :param columns: list of strings
            Columns to which the value is inserted
        :return: None
        """
        query = '''INSERT INTO ''' + table
        query += ''' (''' + ''', '''.join(columns) + ''') '''
        values = ''' VALUES(''' + ''', '''.join([self.check(i) for i in value]) + '''); '''
        # TODO: Replace prints with logging
        print(query+values)
        self.cursor.execute(query + values)
        self.conn.commit()
        # TODO: Replace prints with logging
        print('loaded to ' + str(table))

    @staticmethod
    def check(value):
        """
        Cast value to string

        :param value: any type
            The checked value
        :return: string
            Casts string, if possible
        """
        if type(value) == int:
            return str(value)
        elif type(value) == str:
            value = value.replace('"', '')
            value = ''.join([x for x in value if ord(x)])
            return u''+'''"''' + value + '''"'''
        elif not value:
            return '''NULL'''
        else:
            # TODO: Replace prints with logging
            print(type(value), type)
            raise TypeError("Unknown type")

    def get_db_info(self):
        """
        Get all information about the database

        :return: list of string
            All information about database
        """
        self.cursor.execute("SELECT * FROM sqlite_master WHERE type='table'")
        return self.cursor.fetchall()


if __name__ == '__main__':
    c = DBaseRusNLP("rus_nlp_withouttexts_server_after_update.db", "meta_data.json")
    bd_read_helper = ReaderDBase(c)
    bd_write_helper = WriterDBase(c)

    # c.alter_add_column("conference", "description_ru", "text")
    # c.alter_add_column("conference", "description_en", "text")
    # c.alter_add_column("conference", "conf_id", "INT")
    # c.update("conference", "conf_id", 1, "conference", "Dialogue")
    # c.update("conference", "conf_id", 2, "conference", "AIST")
    # c.update("conference", "conf_id", 3, "conference", "AINL")
    # c.update("conference", "conf_id", 4, "conference", "RuSSIR")
    # descr_ru_d = '''"Диалог" - старейшая и крупнейшая российская конференция по компьютерной лингвистике и обработке естественного языка. Объединяет как лингвистов общего направления так и специалистов по автоматическим методам.\nРегулярно проводится с 1995 года, предшествующие ей семинары проводились с 70-х годов XX века.\nМестоположение: Москва\nСайт: http://www.dialog-21.ru/'''
    # descr_en_d = '''"Dialogue" is the oldest and the largest Russian conference in computational linguistics and NLP. Its participants come both from general linguistics and from automatic language processing communities.\nThe conference is held regularly since 1995, it was preceded by irregular topical workshops since 1970s.\nLocation: Moscow\nWeb page: http://www.dialog-21.ru/'''
    # descr_ru_as = '''AIST - это конференция, посвященная "анализу изображений, социальных сетей и текстов" ("Analysis of Images, Social networks and Texts" - отсюда английская аббревиатура AIST). В основном направлена на специалистов по компьютерным наукам и обработке данных, но доклады по автоматической обработке языка традиционно составляют весьма существенную часть программы.\nРегулярно проводится с 2012 года.\nМестоположение: ранее Екатеринбург, ныне Москва\nСайт: https://aistconf.org/'''
    # descr_en_as = '''AIST is a conference dedicated to the Analysis of Images, Social networks and Texts (hence the AIST abbreviation). It is mostly aimed at computer and data scientists, but has a very strong NLP component.\nAIST is regularly held since 2012.\nLocation: previously Yekaterinburg, recently Moscow\nWeb page: https://aistconf.org/'''
    # descr_ru_an = '''AINL - это конференция по искусственному интеллекту и естественному языка ("Artificial Intelligence and Natural Language"). Заявляется о сильном упоре на практические задачи и демонстрацию реальных приложений, традиционно много докладчиков из индустрии. Многие из организаторов AINL являются специалистами в NLP, и темы, связанны с автоматической обработкой естественного языка являются неотъемлемой частью конференции. AINL активно приглашает к участию студентов.\nРегулярно проводится с 2012 года.\nМестоположение: Санкт-Петербург\nСайт: https://ainlconf.ru/'''
    # descr_en_an = '''AINL is a conference in Artificial Intelligence and Natural Language. It has strong focus on practical tasks, with industrial talks and demos. NLP topics are ubiquitous, with many organizers coming from the NLP community. Students are particularly encourage to participate in AINL\nAINL is regularly held since 2012.\nLocation: Saint Petersburg\nWeb page: https://ainlconf.ru/'''
    # c.update("conference", "description_ru", descr_ru_d, "conference", "Dialogue")
    # c.update("conference", "description_ru", descr_ru_as, "conference", "AIST")
    # c.update("conference", "description_ru", descr_ru_an, "conference", "AINL")
    # c.update("conference", "description_en", descr_en_d, "conference", "Dialogue")
    # c.update("conference", "description_en", descr_en_as, "conference", "AIST")
    # c.update("conference", "description_en", descr_en_an, "conference", "AINL")

    #bd_write_helper.delete_article("ainl_2016_7868559ccb77c5c82fae24a937fa266db151ddf0")

    #bd_write_helper.delete_rows_from_article_by_common_id(["ainl_2016_7868559ccb77c5c82fae24a937fa266db151ddf0"])
    c.cursor.execute("SELECT * FROM conference")
    a = c.cursor.fetchall()
    for i in a:
        print(i)
    # try:
    #     for i in range(18):
    #         bd_write_helper.insert_into_conference([('Dialogue', 2000 + i)])
    #     for i in range(15, 18):
    #         bd_write_helper.insert_into_conference([('AINL', 2000 + i)])
    #     for i in range(7, 18):
    #         bd_write_helper.insert_into_conference([('AIST', 2000 + i)])
    #     for i in range(7, 18):
    #         bd_write_helper.insert_into_conference([('RuSSIR', 2000 + i)])
    # except Exception as e:
    #     print(e)
    # # bd_write_helper.load_to_affiliation_alias_new("affiliations_final.tsv")
    # bd_write_helper.load_to_author_alias_new("new_names.txt")
