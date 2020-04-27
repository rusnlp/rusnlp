import sqlite3
import json


class DBaseRusNLP:
    def __init__(self, db_path, config_file):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('PRAGMA encoding = "UTF-8"')
        self.tables = json.load(open(config_file))
        for name, data in self.tables.items():
            self.create_table(name, data)

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
        constraints = ", " + ", ".join(operations_list[1:]) if len(operations_list) > 1 else ""
        # TODO: Replace prints with logging
        # print(query + columns + last+constraints)
        self.cursor.execute(query + columns + constraints + last)
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
        set_col = ''' SET ''' + column + '''= ''' + self.check(value)
        where = ''' WHERE ''' + what + ''' = ''' + self.check(condition)
        try:
            self.cursor.execute(query + set_col + where)
            self.conn.commit()
        except Exception as e:
            pass
            # TODO: Replace prints with logging
            print(query + set_col + where, e)

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
        print(query + col_query)
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
        query = "DELETE * FROM " + table
        where = "WHERE {} = {}".format(column, self.check(condition))
        self.cursor.execute(query + where)
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

    def select_count(self, where):
        """
        Get amount of articles on the specified language.
        :return: int
            Amount of the articles with the specified language
        """
        what = '''COUNT(DISTINCT id) '''
        where = '''{}'''.format(where)
        result = self.select(what, where)
        return result[0][0]

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
        print(query + values)
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
            value = value.replace("'", """ """).replace('"', """ """)
            value = ''.join([x for x in value if ord(x)])
            return u'' + '''"''' + value + '''"'''
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
