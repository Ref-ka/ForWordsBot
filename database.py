import sqlite3 as lite


class DataBase:
    def __init__(self):
        self.conn = lite.connect("EngTeacher.db", check_same_thread=False)
        self.conn.execute('pragma foreign_keys = on')
        self.conn.commit()
        self.cur = self.conn.cursor()

    def query(self, arg, values=None):
        if values is None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg, values)
        self.conn.commit()

    def fetchone(self, arg, values=None):
        if values is None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg, values)
        return self.cur.fetchone()

    def fetchall(self, arg, values=None):
        if values is None:
            self.cur.execute(arg)
        else:
            self.cur.execute(arg, values)
        return self.cur.fetchall()

    def input_words(self, chat_id, foreign_word, native_word, group, lang):
        # Insert the word with the given group
        self.cur.execute('INSERT INTO words ("chat_id", "foreign_word", "native_word", "group", "lang") VALUES (?, ?, ?, ?, ?)',
                         (chat_id,
                          foreign_word,
                          native_word,
                          group,
                          lang))
        self.conn.commit()

    def get_show_words(self, chat_id, group=None, lang=None):
        if group and lang:
            return self.fetchall(
                'SELECT "foreign_word", "native_word", "group", "lang" FROM words WHERE "chat_id" = (?) AND "group" IN (?) AND "lang" = (?)',
                (chat_id, group, lang))
        elif group and not lang:
            return self.fetchall(
                'SELECT "foreign_word", "native_word", "group", "lang" FROM words WHERE "chat_id" = (?) AND "group" = (?)',
                (chat_id, group))
        elif not group and lang:
            return self.fetchall(
                'SELECT "foreign_word", "native_word", "group", "lang" FROM words WHERE "chat_id" = (?) AND "lang" = (?)',
                (chat_id, lang))
        else:
            return self.fetchall('SELECT "foreign_word", "native_word", "group", "lang" FROM words WHERE "chat_id" = (?)',
                                 (chat_id,))

    def delete_words(self, chat_id: int, word: str):
        self.cur.execute('DELETE FROM words WHERE chat_id = (?) AND eng_word = (?)', (chat_id, word))
        self.conn.commit()

    # def change_word(self, chat_id: int, words: dict):
    #     if words["lang"] == 'en':
    #         self.cur.execute('UPDATE words SET eng_word = ? WHERE chat_id = ? AND eng_word = ?',
    #                          (words['changed'], chat_id, words['changeable']))
    #     elif words["lang"] == 'ru':
    #         self.cur.execute('UPDATE words SET ru_word = ? WHERE chat_id = ? AND eng_word = ?',
    #                          (words['changed'], chat_id, words['changeable']))
    #     elif words["lang"] == 'group':
    #         # Update the group for the word identified by its foreign word
    #         self.cur.execute('UPDATE words SET "group" = ? WHERE chat_id = ? AND eng_word = ?',
    #                          (words['changed'], chat_id, words['word']))
    #     self.conn.commit()

    # def change_word(self, chat_id: int, ):

    def get_word_for_editing(self, chat_id: int, native_word: str, lang: str):
        self.cur.execute('SELECT "foreign_word", "native_word", "group", "lang" FROM words WHERE "chat_id" = (?) AND "native_word" = (?) AND "lang" = (?)',
                         (chat_id, native_word, lang))
        return self.cur.fetchall()

    def change_native_word(self, chat_id: int, old_native_word: str, new_native_word: str, lang="all"):
        if lang == "all":
            self.cur.execute(
                'UPDATE words SET native_word = (?) WHERE chat_id = (?) AND native_word = (?) AND lang = (?)',
                (chat_id, new_native_word, old_native_word))
        else:
            self.cur.execute(
                'UPDATE words SET native_word = (?) WHERE chat_id = (?) AND native_word = (?) AND lang = (?)',
                (chat_id, new_native_word, old_native_word, lang))
        self.conn.commit()

    def change_foreign_word(self, chat_id: int, native_word: str, foreign_word: str, lang: str):
        self.cur.execute('UPDATE words SET foreign_word = (?) WHERE chat_id = (?) AND native_word = (?) AND lang = (?)',
                         (foreign_word, chat_id, native_word, lang))
        self.conn.commit()

    def change_group(self, chat_id: int, native_word: str, group: str, lang: str):
        self.cur.execute('UPDATE words SET group = (?) WHERE chat_id = (?) AND native_word = (?) AND lang = (?)',
                         (group, chat_id, native_word, lang))
        self.conn.commit()

    def chang_lang_code(self, chat_id: int, native_word: str, old_lang: str, new_lang: str):
        self.cur.execute('UPDATE words SET lang = (?) WHERE chat_id = (?) AND native_word = (?) AND lang = (?)',
                         (chat_id, new_lang, native_word, old_lang))
        self.conn.commit()

    def get_words_by_group(self, chat_id, group):
        # Fetch words for the specified group and chat_id
        return self.fetchall('SELECT "foreign_word", "native_word", "group", "lang" FROM words WHERE chat_id = ? AND "group" = ?', (chat_id, group))

    def __del__(self):
        self.conn.close()
