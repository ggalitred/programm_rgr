import sqlite3
import math
import re
from datetime import datetime

from flask import url_for


class FDataBase:
    def __init__(self, db):
        self.__db = db
        self.__cur = db.cursor()

    def addRevokedToken(self, token):
        try:
            self.__cur.execute("INSERT INTO revoked_tokens VALUES(NULL, ?)", (token,))
            self.__db.commit()
        except sqlite3.Error as e:
            print("Ошибка добавления пользователя: " + str(e))
            return False
        return True

    def getToken(self, token):
        try:
            self.__cur.execute("SELECT COUNT() as `count` FROM revoked_tokens WHERE token = ?", (token,))
            res = self.__cur.fetchone()
            print("COUNT: " + str(res['count']))
            if res['count'] == 0:
                return False
            else:
                return True
        except sqlite3.Error as e:
            print("Ошибка добавления пользователя: " + str(e))
            return False

    def addUser(self, surname, name, patronymic, email, hpass):
        print("adduser reached")
        try:
            self.__cur.execute("SELECT COUNT() as `count` FROM users WHERE email LIKE ?", (email,))
            res = self.__cur.fetchone()
            if res['count'] != 0:
                print("Такой пользователь уже есть!")
                return False

            self.__cur.execute("INSERT INTO users VALUES(NULL, ?, ?, ?, ?, ?, ?)",
                               (surname, name, patronymic, email, hpass, "user"))
            self.__db.commit()
        except sqlite3.Error as e:
            print("Ошибка добавления пользователя: " + str(e))
            return False

        return True

    def getUser(self, user_id):
        try:
            self.__cur.execute("SELECT * FROM users WHERE id = ? LIMIT 1", (user_id,))
            res = self.__cur.fetchone()
            if not res:
                print("Пользователь не найден")
                return False

            return res

        except sqlite3.Error as e:
            print("Ошибка " + str(e))
        return False

    def getUserByApplicationID(self, application_id):
        try:
            self.__cur.execute("SELECT user_id FROM applications WHERE id = ?", (application_id,))
            user_id = int(self.__cur.fetchone()[0])

            print("Userid: " + str(user_id))


            self.__cur.execute("SELECT surname, name, patronymic FROM users WHERE id = ?", (user_id,))
            res = self.__cur.fetchone()
            return res
        except sqlite3.Error as e:
            print("Ошибка: " + str(e))
            return False

    def getUserByEmail(self, email):
        try:
            self.__cur.execute("SELECT * FROM users WHERE email = ? LIMIT 1", (email,))
            res = self.__cur.fetchone()
            if not res:
                print("Пользователь не найден")
                return None

            return res
        except sqlite3.Error as e:
            print("Ошибка получения данных " + str(e))

        return False

    def addCase(self, description):
        try:
            self.__cur.execute("INSERT INTO cases VALUES(NULL, ?)", (description,))
            self.__db.commit()

        except sqlite3.Error as e:
            print("Ошибка добавления дела в базу данных: " + str(e))
            return False

        return True

    def addApplication(self, user_id, case_id):
        try:
            self.__cur.execute("SELECT COUNT(*) FROM applications WHERE user_id = ? AND case_id = ? and app_status = ?",
                               (user_id, case_id, "wait"))
            count = self.__cur.fetchone()[0]
            if count > 0:
                print(count)
                print("Такая заявка уже существует!")
                return False
            self.__cur.execute(
                "INSERT INTO applications VALUES(NULL, ?, ?, ?, strftime('%d-%m-%Y %H:%M', datetime('now')))", \
                (user_id, case_id, "wait"))
            self.__db.commit()
        except sqlite3.Error as e:
            print("Ошибка добавления заявки: " + str(e))
            return False

        return True

    def getApplicationsList(self):
        try:
            self.__cur.execute("SELECT * FROM applications WHERE app_status = \"wait\"")
            self.__db.commit()
            rows = self.__cur.fetchall()
        except sqlite3.Error as e:
            print("Ошибка получения заявки: " + str(e))
            return False

        return rows

    def getApplicationsByUserID(self, user_id):
        try:
            self.__cur.execute("SELECT * FROM applications WHERE user_id = ?", (user_id,))
            self.__db.commit()
            rows = self.__cur.fetchall()

        except sqlite3.Error as e:
            print("Ошибка добавления заявки: " + str(e))
            return False

        return rows

    def getApplicationInfo(self, case_id):
        try:
            self.__cur.execute("SELECT description FROM cases WHERE id = ?", (case_id,))
            self.__db.commit()
            rows = self.__cur.fetchall()

        except sqlite3.Error as e:
            print("Ошибка добавления заявки: " + str(e))
            return False

        return rows[0]

    def setApplicationStatus(self, app_id, app_status):
        try:
            self.__cur.execute("UPDATE applications SET app_status = ? WHERE id = ?", (app_status, app_id,))
            self.__db.commit()
        except sqlite3.Error as e:
            print("Ошибка обновления заявки: " + str(e))
            return False

        return True

    def getNews(self, news_count=None):
        print(news_count)
        try:
            if news_count is not None:
                self.__cur.execute(
                    "SELECT id, news_article, news_text, news_date FROM news ORDER BY id DESC LIMIT ?",
                    (news_count,))
            else:
                self.__cur.execute(
                    "SELECT id, news_article, news_text, news_date FROM news ORDER BY id DESC")
            self.__db.commit()
            rows = self.__cur.fetchall()
        except sqlite3.Error as e:
            print("Ошибка получения новостей: " + str(e))
            return False
        return rows

    def getOneNews(self, news_id):
        try:
            self.__cur.execute("SELECT news_article, news_text, news_date FROM news WHERE id = ?", (news_id,))
            self.__db.commit()
            rows = self.__cur.fetchall()

        except sqlite3.Error as e:
            print("Ошибка получения новости: " + str(e))
            return False
        return rows[0]

    def addCommentary(self, news_id, author, comment):
        try:
            self.__cur.execute("INSERT INTO commentaries VALUES(NULL, ?, ?, ?)", (news_id, author, comment,))
            self.__db.commit()
        except sqlite3.Error as e:
            print("Ошибка добавления комментария: " + str(e))
            return False

        return True

    def getCommentaries(self, news_id):
        try:
            self.__cur.execute("SELECT author, comment FROM commentaries WHERE news_id = ?", (news_id,))
            self.__db.commit()
            rows = self.__cur.fetchall()
        except sqlite3.Error as e:
            print("Ошибка получения комментариев: " + str(e))
            return False

        return rows

    def getCases(self):
        try:
            self.__cur.execute("SELECT id FROM cases")
            rows = self.__cur.fetchall()
        except sqlite3.Error as e:
            print("Ошибка получения списка дел: " + str(e))
            return False
        return rows

    def addNews(self, news_article, news_text, case_id):
        try:
            if news_text != '' and news_article != '':
                current_time = datetime.now().strftime('%H:%M, %d-%m-%Y')
                self.__cur.execute("INSERT INTO news VALUES(NULL, ?, ?, ?, ?)",
                                   (news_article, news_text, case_id, current_time,))
                self.__db.commit()
        except sqlite3.Error as e:
            print("Ошибка добавления новости: " + str(e))
            return False

        return True

    def getNewsForPages(self, page_id):
        try:
            self.__cur.execute("SELECT * FROM (SELECT *, ROW_NUMBER() OVER (ORDER BY id DESC) AS row_num FROM news) AS "
                               "subquery WHERE row_num BETWEEN (? - 1) * 10 + 1 AND ? * 10", (page_id, page_id,))
            rows = self.__cur.fetchall()
        except sqlite3.Error as e:
            print("Ошибка получения новостей: " + str(e))
            return False
        return rows
