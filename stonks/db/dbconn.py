import sqlite3
from os import getcwd as path


class DbConn:
    def __init__(self):
        self.conn = sqlite3.connect(path() + r"/db/stocks.db")
        self.create_tables()

    def create_tables(self):
        self.conn.execute(
            'CREATE TABLE IF NOT EXISTS holdings ('
            'stock    TEXT,'
            'owned_by     INTEGER,'
            'quantity   INTEGER'
            ')'
        )

        self.conn.execute(
            'CREATE TABLE IF NOT EXISTS profile ('
            'user    INTEGER,'
            'money     REAL,'
            'handle   TEXT'
            ')'
        )

        self.conn.execute(
            'CREATE TABLE IF NOT EXISTS ratings ('
            'handle    TEXT,'
            'rating     INTEGER'
            ')'
        )
        self.conn.commit()

    def get_market_stocks(self):
        query = '''SELECT stock, quantity FROM holdings where owned_by = -1 and quantity != 0'''
        return [(k[0], k[1]) for k in self.conn.execute(query).fetchall()]

    def get_user_stocks(self, user):
        query = '''SELECT stock, quantity FROM holdings where owned_by = ? and quantity != 0'''
        return [(k[0], k[1]) for k in self.conn.execute(query, (user,)).fetchall()]

    def get_all_users(self):
        query = '''
                            SELECT owned_by from holdings where owned_by != -1
                        '''
        return set([int(k[0]) for k in self.conn.execute(query).fetchall()])

    def get_stock(self, stock):
        query = '''
                            SELECT owned_by, quantity from holdings where upper(stock)=?
                        '''
        return [(k[0], k[1]) for k in self.conn.execute(query, (stock.upper(),)).fetchall()]

    def get_all_handles(self):
        query = '''
                            SELECT handle from profile
                        '''
        return [(k[0]) for k in self.conn.execute(query).fetchall()]

    def check_handle_exists(self, handle):
        query = '''
                        SELECT handle from profile where upper(handle)=?
                        '''
        return len([(k[0]) for k in self.conn.execute(query, (handle.upper(),)).fetchall()]) > 0

    def create_profile(self, user, handle, rating):
        query1 = '''
                    INSERT INTO profile
                    (user, money, handle)
                    VALUES
                    (?, ?, ?)
                '''
        query2 = '''
                    INSERT INTO holdings
                    (stock, owned_by, quantity)
                    VALUES
                    (?, ?, ?)
                '''
        query3 = '''
                            INSERT INTO ratings
                            (handle, rating)
                            VALUES
                            (?, ?)
                        '''

        cur = self.conn.cursor()
        cur.execute(query1, (user, 20.0, handle))
        cur.execute(query2, (handle, user, 100))
        cur.execute(query2, (handle, -1, 0))
        cur.execute(query3, (handle, rating))
        self.conn.commit()

    def update_rating(self, handle, rating):
        query = '''
                    UPDATE ratings SET rating=? where upper(handle)=?
                        '''
        cur = self.conn.cursor()
        cur.execute(query, (rating, handle.upper(),))
        self.conn.commit()

    def update_market(self, stock, new):
        query = '''UPDATE holdings SET quantity=? where owned_by=-1 and upper(stock)=?'''
        cur = self.conn.cursor()
        cur.execute(query, (new, stock.upper(),))
        self.conn.commit()

    def create_holding(self, owned_by, stock, quantity):
        query = '''
                            INSERT INTO holdings
                            (stock, owned_by, quantity)
                            VALUES
                            (?, ?, ?)
                        '''
        cur = self.conn.cursor()
        cur.execute(query, (stock, owned_by, quantity))
        self.conn.commit()

    def get_rating(self, handle):
        query = '''
                    SELECT rating from ratings where upper(handle)=?
                '''
        return self.conn.execute(query, (handle.upper(),)).fetchone()[0]

    def get_balance(self, user):
        query = '''
                    SELECT money from profile where user=?
                '''
        return self.conn.execute(query, (user,)).fetchone()[0]

    def get_all_holdings(self):
        query = '''SELECT * from holdings where owned_by != -1'''
        return [(k[0], k[1], k[2]) for k in self.conn.execute(query).fetchall()]

    def get_owners(self, stock):
        query = '''SELECT owned_by, quantity from holdings where upper(stock)=?'''
        return [(k[0], k[1]) for k in self.conn.execute(query, (stock.upper(),)).fetchall()]

    def set_balance(self, user, balance):
        query = '''UPDATE profile set money=? where user=?'''
        cur = self.conn.cursor()
        cur.execute(query, (round(balance, 2), user,))
        self.conn.commit()

    def update_holding(self, user, stock, new):
        query = '''UPDATE holdings set quantity=? where owned_by=? and upper(stock)=?'''
        cur = self.conn.cursor()
        cur.execute(query, (new, user, stock.upper()))
        self.conn.commit()

    def update_handle(self, user, old, new):
        query = '''UPDATE holdings set stock=? where upper(stock)=?'''
        query2 = '''UPDATE profile set handle=? where user=?'''
        query3 = '''UPDATE ratings set handle=? where upper(handle)=?'''
        cur = self.conn.cursor()
        cur.execute(query, (new, old.upper()))
        cur.execute(query2, (new, user))
        cur.execute(query3, (new, old.upper()))
        self.conn.commit()

    def get_handle(self, user):
        query = '''
                    SELECT handle from profile where user=?
                '''
        try:
            return self.conn.execute(query, (user,)).fetchone()[0]
        except Exception:
            return None
