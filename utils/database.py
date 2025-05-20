import sqlite3 as lite


class DataBase:
    def __init__(self):
        self.conn = lite.connect("utils/EngTeacher.db", check_same_thread=False)
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

    def input_word(self, chat_id, foreign_word, lang, native_word, group):
        # Insert the word with the given group
        self.cur.execute('INSERT INTO words ("chat_id", "foreign_word", "native_word", "group", "lang") VALUES (?, ?, ?, ?, ?)',
                         (chat_id,
                          foreign_word,
                          native_word,
                          group,
                          lang))
        self.conn.commit()

    def get_show_words(self, chat_id, groups: list = None, langs: list = None):
        if not groups:
            groups = []
        if not langs:
            langs = []
        groups_placeholders = ", ".join(["?"] * len(groups))
        langs_placeholders = ", ".join(["?"] * len(langs))
        params = tuple([chat_id] + groups + langs)
        if groups and langs:
            return self.fetchall(
                f'SELECT "foreign_word", "native_word", "group", "lang" '
                f'FROM words WHERE "chat_id" = (?) '
                f'AND "group" IN ({groups_placeholders}) AND "lang" = ({langs_placeholders})',
                params)
        elif groups and not langs:
            return self.fetchall(
                f'SELECT "foreign_word", "native_word", "group", "lang" '
                f'FROM words WHERE "chat_id" = (?) AND "group" = ({groups_placeholders})',
                params)
        elif not groups and langs:
            return self.fetchall(
                f'SELECT "foreign_word", "native_word", "group", "lang" '
                f'FROM words WHERE "chat_id" = (?) AND "lang" = ({langs_placeholders})',
                params)
        else:
            return self.fetchall(
                'SELECT "foreign_word", "native_word", "group", "lang" FROM words WHERE "chat_id" = (?)',
                params)

    def delete_word(self, chat_id: int, native: str, lang: str):
        self.cur.execute('DELETE FROM words WHERE chat_id = (?) AND native_word = (?) AND lang = (?)',
                         (chat_id, native, lang))
        self.conn.commit()

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
        print(group)
        self.cur.execute('UPDATE words SET "group" = (?) WHERE "chat_id" = (?) AND "native_word" = (?) AND "lang" = (?)',
                         (group, chat_id, native_word, lang))
        self.conn.commit()

    def change_lang_code(self, chat_id: int, native_word: str, new_lang: str, old_lang: str):
        self.cur.execute('UPDATE words SET lang = (?) WHERE chat_id = (?) AND native_word = (?) AND lang = (?)',
                         (new_lang, chat_id, native_word, old_lang))
        self.conn.commit()

    def get_words_by_group(self, chat_id, group):
        # Fetch words for the specified group and chat_id
        return self.fetchall('SELECT "foreign_word", "native_word", "group", "lang" '
                             'FROM words WHERE chat_id = ? AND "group" = ?',
                             (chat_id, group))

    def get_flash_words(self, user_id, groups=None, languages=None):
        query = 'SELECT "foreign_word", "native_word", "group", "lang" FROM "words" WHERE "chat_id" = ?'
        params = [user_id]

        # Apply filters
        if groups and len(groups) > 0:
            placeholders = ", ".join(["?"] * len(groups))
            query += f' AND "group" IN ({placeholders})'
            params.extend(groups)

        if languages and len(languages) > 0:
            placeholders = ", ".join(["?"] * len(languages))
            query += f' AND "lang" IN ({placeholders})'
            params.extend(languages)
        print(params)

        self.cur.execute(query, params)
        return self.cur.fetchall()

    def __del__(self):
        self.conn.close()
