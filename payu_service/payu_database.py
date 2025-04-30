import sqlite3, threading

db = sqlite3.connect("payments.db", check_same_thread=False)
db.row_factory = sqlite3.Row

lock = threading.Lock()

def initialize_database():
	cursor = db.cursor()

	cursor.execute(
"""CREATE TABLE IF NOT EXISTS payments (
	orderId VARCHAR(36) NOT NULL PRIMARY KEY,
	payuId VARCHAR(128) NOT NULL,
	userId VARCHAR(128) NOT NULL,
	internalId VARCHAR(36) NOT NULL,
	amount INTEGER NOT NULL,
	mail VARCHAR(128) NOT NULL,
	userName VARCHAR(128) NOT NULL,
	status VARCHAR(16) NOT NULL
);""")
	cursor.close()
	db.commit()
	
def get_payment_by_order_id(orderId):
	with lock:
		cursor = db.cursor()
		result = cursor.execute("SELECT * FROM payments WHERE orderId = ?;", (orderId,)).fetchone()
		cursor.close()
		return dict(result)

def get_payments_by_user_id(userId):
	with lock:
		cursor = db.cursor()
		result = cursor.execute("SELECT * FROM payments WHERE userId = ?;", (userId,)).fetchall()
		cursor.close()
		return [dict(row) for row in result]

def insert_payment(orderId, payuId, userId, internalId, amount, mail, userName):
	with lock:
		cursor = db.cursor()
		cursor.execute(
			"INSERT INTO payments(orderId, payuId, userId, internalId, amount, mail, userName, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
			(orderId, payuId, userId, internalId, amount, mail, userName, "CREATED")
		)
		cursor.close()
		db.commit()

def update_payment(orderId, status):
	with lock:
		cursor = db.cursor()
		cursor.execute("UPDATE payments SET status = ? WHERE orderId = ?;", (status, orderId))
		cursor.close()
		db.commit()