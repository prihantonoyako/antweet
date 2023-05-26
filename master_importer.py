import pandas as pd
import sqlite3

df = pd.read_csv('./Data-Training-IKN.csv')
df.dropna(inplace = True)

conn = sqlite3.connect('db.sqlite3')
cur = conn.cursor()
cur.executemany("INSERT INTO unprocessed_data (full_text, created_at, username, user_created_at) VALUES(?,?,?,?)", list(df[['full_text', 'created_at', 'user/name','user/created_at']].to_records(index=False)))
conn.commit()
conn.close()