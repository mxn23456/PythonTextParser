import text_parser
import sqlite3
import datetime
import re

dbName = "database.db"

monthsConversion={"January":1, "February":2,"March":3,"April":4,
                  "May":5,"June":6,"July":7,"August":8,"September":9,
                  "October":10,"November":11,"December":12}

#Require: asset_description for vehicles has String format: "year make model color VIN"
#Note on future reinforcement: consider reference key and primary key
def setUpDatabase():
	try:
		conn =sqlite3.connect(dbName)
		c= conn.cursor()
		c.executescript("""
			DROP TABLE IF EXISTS asset_transactions;
			DROP TABLE IF EXISTS assets;
			CREATE TABLE asset_transactions(amount INT,trans_desc TEXT, date TEXT, asset_id INT);
			CREATE TABLE assets(asset_description TEXT, date_purchased TEXT, date_sold TEXT, notes BLOB, pictures BLOB);""")
		conn.commit()
	except sqlite3.Error:
		if conn:
			conn.rollback()
			print ("There was an error with the SQL")
	finally:
		if conn:
			conn.close()

def addAsset (asset_description,date_purchased,date_sold,notes,pictures):
	try:	
		conn =sqlite3.connect(dbName)
		c= conn.cursor()
		if not assetExisted(asset_description,c):
			#if date_purchased == None: Not needed
			#	date_purchased=str(datetime.date.today())
			c.execute("INSERT INTO assets VALUES(?,?,?,?,?)",(asset_description,date_purchased,date_sold,notes,pictures))
			conn.commit()
			print("added asset")
			#print("Added asset description: "+asset_description+"; date purchased: " + str(date_purchased) + "; date_sold: " + str(date_sold) + "; notes: " + str(notes) + "; pictures: " + str(pictures))
		elif date_sold:
			c.execute("UPDATE assets SET date_sold=? WHERE asset_description=?",(date_sold,asset_description))
			conn.commit()
			print("updated asset's sold date")
			#print("Updated sold date of asset descritpion: "+asset_description+" to sold date: " + date_sold)	
		else:
			#print("Error: Cannot Add asset with description: "+asset_description+". Already existed")
			print("did not add asset")
	except sqlite3.Error as e:
		if conn:
			print("An error occurred:", e.args[0])
	finally:
		if conn:
			conn.close()

def assetExisted(asset_description,cursor):
	#idea: if asset is a vehicle, find a way to parse through the statements and find it
	cursor.execute("SELECT * FROM assets WHERE asset_description=?",(asset_description,))
	result = cursor.fetchone()
	if result:
		return True
	else:
		return False

#Note: asset_description will be referenced from asset_transactions table via its rowid. If asset_description does not match any record in assets table, its rowid will be assigned to 0, meaning it is an abandon or pending transaction waiting to be reconciled.
def addTransaction(amount,trans_desc, date, asset_description):
	try:
		conn =sqlite3.connect(dbName)
		c= conn.cursor()
		if not transactionExisted(c,amount,trans_desc,asset_description,date):
			asset_id = getAssetRowid(asset_description,c)
			c.execute("INSERT INTO asset_transactions VALUES(?,?,?,?)",(amount,trans_desc, date, asset_id))
			conn.commit()
			print("added transaction")
		else:
		#	print("Cannot add transaction, already existed")
			print("did not add transaction")
	except sqlite3.Error as e:
		if conn:
			print("An error occurred:", e.args[0])
	finally:
		if conn:
			conn.close()

def transactionExisted(cursor,amount,trans_desc,asset_description,date):
	asset_id = getAssetRowid(asset_description,cursor)
	if asset_description == "Supplies" or asset_description == "Bills" or asset_description == "Labor":
		print("Adding non recoverable transaction to asset_description: " + asset_description)
		cursor.execute("SELECT * FROM asset_transactions WHERE trans_desc = ? AND amount = ? AND asset_id = ? AND date = ?",(trans_desc,amount,asset_id, date))
	else:
		print("Adding recoverable transaction to asset_descrtiption: " + asset_description)
		cursor.execute("SELECT * FROM asset_transactions WHERE trans_desc = ? AND amount = ? AND asset_id = ? ",(trans_desc,amount,asset_id))

	result = cursor.fetchone()
	if result:
		return True
	else:
		return False

#Return row id if asset_description matches, otherwise return 0
def getAssetRowid(asset_description,cursor):
	cursor.execute("SELECT rowid FROM assets WHERE asset_description=?",(asset_description,))
	result = cursor.fetchone()
	if result:
		return result[0]
	else:
		return 0

def getAssetsTable():
	try:
		conn =sqlite3.connect(dbName)
		c= conn.cursor()
		c.execute("SELECT * FROM assets")
		data = c.fetchall()
		return data
	except sqlite3.Error as e:
		if conn:
			print("An error occurred:", e.args[0])
	finally:
		if conn:
			conn.close()

def getAssetTransactionsTable():
	try:
		conn =sqlite3.connect(dbName)
		c= conn.cursor()
		c.execute("SELECT * FROM asset_transactions")
		data = c.fetchall()
		return data
	except sqlite3.Error as e:
		if conn:
			print("An error occurred:", e.args[0])
	finally:
		if conn:
			conn.close()

def getAssetTransactions (asset_description):
	try:
		conn =sqlite3.connect(dbName)
		cursor= conn.cursor()
		asset_id=getAssetRowid(asset_description,cursor)
		cursor.execute("SELECT * FROM asset_transactions WHERE asset_id=?",(asset_id,))
		data = cursor.fetchall()
		return data
	except sqlite3.Error as e:
		if conn:
			print("An error occurred:", e.args[0])
	finally:
		if conn:
			conn.close()

def addTextFileToDB2(fileName,year):
	lines = text_parser.getLines(fileName)
	lines = text_parser.parseMonthlyStatement(0,len(lines) - 1,lines)

	beginOfAsset=re.compile("^-{2,}.+")
	beginOfMonths=re.compile("\((January|February|March|April|May|June|July|August|September|October|November|December)\)")	
	closedDealsGroup=re.compile("^(\/{2,})(\-{2,})Closed Deals")
	beginOfGroup = re.compile("^(\/{2,})(\-{2,}).+$")
	isATransaction = re.compile("^(\+|-)\d+\s")

	currentGroup = ""
	currentAsset = ""
	currentMonthNumber = 0
	date_sold = ""
	asset_description = ""
	date_purchased = "" #rename this word bc this date also accounted for date sold, date of transaction, and date purchased

	currentLineIndex = 0

	while currentLineIndex < len(lines):
		line = lines[currentLineIndex]
		if beginOfMonths.search(line):
			month = beginOfMonths.search(line).group().replace("(","").replace(")","") #get month name from line
			currentMonthNumber = monthsConversion[month]
			#print ("\n\n          *******Begin of Month: " + month + " ************\n\n")
		elif beginOfGroup.search(line):
			if closedDealsGroup.search(line):
				date_sold = str(datetime.date(year,currentMonthNumber,15)) #set day to default 15
			else:
				date_sold = None
			#print("\n"+line)
		elif beginOfAsset.search(line):
			print("add asset:")
			asset_description = getAssetDescription(line)
			date_purchased = str(datetime.date(year,currentMonthNumber,15)) #set to default 15
			addAsset (asset_description,date_purchased,date_sold,None,None)
		elif isATransaction.search(line):
			print("add transaction:")
			amount = getTransactionAmount(line)
			trans_desc = getTransactionDescription(line)
			date = date_purchased #For now, consider the date to be date_purchased. In future, maybe the line can be parsed and get more exact date
			addTransaction(amount,trans_desc, date, asset_description)
		#else:
			#if not line == "\n":
				#print("Did not perform any action with this line: ",line)
		currentLineIndex = currentLineIndex + 1


def getTransactionDescription(line):
	transactionAmountPattern = re.compile("^(\+|-)\d+\s")
	assetIdentifierPattern = re.compile(";.+$") #Note: Consider space before the semicolon. Maybe make another pattern that replace "\s*\n" with "\n"
	line = re.sub(transactionAmountPattern,"",line)
	line = re.sub(assetIdentifierPattern,"",line)
	#Note: assume that after removing the transaction amount and the ";" along with the asset identifier, 
	#	the remaining string does not have any space infront and after it
	return line	
			
							
def getTransactionAmount(line):
	number = re.compile("^(\+|-)\d+\s")
	result = int(number.search(line).group().replace(" ",""))
	return result

def getAssetDescription(line):
	subtotalPattern = re.compile("\s*\((\+|-)?\d+\)\s*")
	assetMarkPattern = re.compile("^-{2,}")
	line = re.sub(subtotalPattern,"",line)
	line = re.sub(assetMarkPattern,"",line)
	return line

def getTransactionsOfAsset(assetDescription):
	try:
		conn =sqlite3.connect(dbName)
		c= conn.cursor()
		asset_id = getAssetRowid(assetDescription,c)
		c.execute("SELECT * FROM asset_transactions WHERE asset_id = ?",(asset_id,))
		data = c.fetchall()
		return data
	except sqlite3.Error as e:
		if conn:
			print("An error occurred:", e.args[0])
	finally:
		if conn:
			conn.close()

def exportMonthlyCashFlow(year):
	"""
	Algorithm:
	1) get the sum of transaction for a asset each month
		a) SQL: get all assets descriptions and their id (2 coloums)
		a2) iterate and get transaction amount and asset_id by months
			for each month, get the id and sum their transaction
		b) for each asset_id, iterate and sum all of the transactions
	2) save it into an array: 0 index is asset desc, 1=jan, 2=feb, ...
	"""
	#assets = []
	try:
		conn =sqlite3.connect(dbName)
		c= conn.cursor()
		c.execute("SELECT rowid,asset_description FROM assets")
		assets = c.fetchall()
		csvTable = []
		csvTable.append(["Assets Description", "January", "February", "March", "April","May","June","July","August","September","October","November","December"])
		for asset in assets:
			print("Asset: " + asset[1])  
			c.execute("SELECT amount, trans_desc, date FROM asset_transactions WHERE asset_id=?",(asset[0],))
			trans = c.fetchall()
			monthlyTransTotal = [0] * 13
			monthlyTransTotal[0] = asset[1] #set index 0 to asset description
			#print(monthlyTransTotal)
			
			#following is raw implementation. Could this be faster?
			for tran in trans:
				#print(tran)
				#total = 0
				currentMonth = 1
				print(tran)
				while currentMonth <= 12:
					#print("enter loop 3")
					dateArray = tran[2].split('-')
					"""
					print("dateArray: ")
					print(dateArray)
					print("dateArray[0]: " + dateArray[0])
					print("dateArray[1]: " + dateArray[1])
					print("currentMonth: " + str(currentMonth))
					"""
					if int(dateArray[1]) == currentMonth and int(dateArray[0]) == year:
						#print("equal")
						monthlyTransTotal[currentMonth] = monthlyTransTotal[currentMonth] + tran[0] #Note: maybe an error if tran[0] is not type int
					currentMonth = currentMonth + 1
			print(monthlyTransTotal)
			csvTable.append(monthlyTransTotal)
			print("total: " + str(getMonthlySummary(monthlyTransTotal)))
			#printTable(trans)							
			#c.execute("SELECT total(amount) FROM asset_transactions WHERE asset_id=?",(asset[0],))
			#print("Sum: "+ str(c.fetchone()[0]))
			print()
		return csvTable
	except sqlite3.Error as e:
		if conn:
			print("An error occurred:", e.args[0])
	finally:
		if conn:
			conn.close()

def getMonthlySummary(monthlyTransTotal):
	m=1
	total = 0
	while m <= 12:
		total = total + monthlyTransTotal[m]
		m = m + 1
	return total

def printTable(data):
	for row in data: #note: if data is blank, there might be a problem.
		print(row)

#---------END DATABASE INTEGRATION

