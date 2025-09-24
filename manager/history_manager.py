import sqlite3


class HistoryManager:
    def __init__(self, db_file="history.db", max_history=1000):
        self.conn = sqlite3.connect(db_file)
        self.max_history = max_history
        self.creat_table()

    def creat_table(self):
        cur = self.conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS history
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           cmd
                           TEXT,
                           hex_flag
                           INTEGER
                           default
                           0,
                           append_enter_flag
                           INTEGER
                           default
                           0,
                           ts
                           TIMESTAMP
                           DEFAULT
                           CURRENT_TIMESTAMP
                       )""")
        self.conn.commit()

    def save_history(self, cmd, hex_flag, append_enter_flag):
        """保存历史记录"""
        print(f"保存历史记录: {cmd}, {hex_flag}, {append_enter_flag}")
        cur = self.conn.cursor()

        # 避免连续重复
        row = cur.execute("SELECT cmd, hex_flag, append_enter_flag FROM history ORDER BY id DESC LIMIT 1").fetchone()
        if row and row[0] == cmd and row[1] == hex_flag and row[2] == append_enter_flag:
            return

        # 删除旧的相同记录
        cur.execute("DELETE FROM history WHERE cmd=? and hex_flag=? and append_enter_flag=?",
                    (cmd, hex_flag, append_enter_flag))
        # 插入新记录
        cur.execute("INSERT INTO history (cmd, hex_flag, append_enter_flag) VALUES (?, ?, ?)",
                    (cmd, hex_flag, append_enter_flag))
        self.conn.commit()

        # 保留最新 max_history 条
        row_count = cur.execute("SELECT COUNT(*) FROM history").fetchone()[0]
        if row_count > self.max_history:
            cur.execute("""DELETE
                           FROM history
                           WHERE id NOT IN (SELECT id
                                            FROM history
                                            ORDER BY id DESC LIMIT ?
                               )""", (self.max_history,))
            self.conn.commit()

    def load_history(self):
        """返回最近 max_history 条历史命令"""
        cur = self.conn.cursor()
        return [row for row in cur.execute(
            "SELECT cmd, hex_flag, append_enter_flag FROM history ORDER BY id asc LIMIT ?", (self.max_history,)
        )]

    def clear_history(self):
        """清空历史记录"""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM history")
        self.conn.commit()

    def close(self):
        self.conn.close()

    def delete_history(self, cmd, hex_flag, append_enter_flag):
        """删除指定历史记录"""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM history WHERE cmd=? and hex_flag=? and append_enter_flag=?",
                    (cmd, hex_flag, append_enter_flag))
        self.conn.commit()
