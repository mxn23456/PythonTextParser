import json
import requests
import urllib
import tp_db_interface

host="http://localhost:3000/"
user_email="remote_login@email.com"
user_token="P9qYRoCGoB5vG-xk_iXM"

def setHost(url):
	global host
	host=url

#Require: type(investment_desc) == str
#	  type(notes) == str
def addInvestment(investment_desc, notes):
	url = host + "investments.json"
	payload = {"investment":{"investment_desc":investment_desc,"notes":notes}}
	return postPayload(url,payload)
	
def updateInvestmentsAtRailsDb():
	investments = tp_db_interface.getAssetsTable()
	for investment in investments:
		investment_desc = investment[0]
		notes = investment[3]
		print("----Adding: ")
		print(investment)		
		result = addInvestment(investment_desc,notes)
		print(result.reason)

def addInvestmentTransaction(investment_desc,amount,transaction_desc, transaction_date):
	url = host + "investments/" + investment_desc + "/investment_transactions.json"
	payload = {"investment_transaction":{"investment_desc":investment_desc,"amount":amount,"transaction_desc":transaction_desc,"transaction_date":transaction_date}}
	return postPayload(url,payload)

def updateInvestmentTransactionsAtRails():
	investments = tp_db_interface.getAssetsTable()
	for investment in investments:
		investment_desc = investment[0]


		print(">>>>>adding transaction for investment: " + investment_desc)
		#print(investment_desc)
		investmentTransactions = tp_db_interface.getAssetTransactions(investment_desc)


		for transaction in investmentTransactions:
				amount = transaction[0]
				transaction_desc = transaction[1]
				transaction_date = transaction[2]
				print("-----Investment: " + investment_desc)
				print("About to add investment transaction :"+transaction_desc +"; Amount: " + str(amount))
				result = addInvestmentTransaction(investment_desc,amount,transaction_desc, transaction_date)
				print("Added attempted; result is: " + result.reason)

def postPayload(url, payload):
	headers = {'content-type': 'application/json','X-User-Email': user_email, 'X-User-Token': user_token}
	print("Hearder: " + str(headers))
	response = requests.post(url, data=json.dumps(payload), headers=headers)
	return response
		
def removeInvestment(investment_desc):
	return None


#------------------------Adding stuff for Inv and Inv_Trans
def addInv(inv_desc, notes):
	url = host + "invs.json"
	payload = {"inv":{"inv_desc":inv_desc,"notes":notes}}
	return postPayload(url,payload)

def updateInvsAtRailsDb():
	invs = tp_db_interface.getAssetsTable()
	for inv in invs:
		inv_desc = inv[0]
		notes = inv[3]
		print("----Adding: ")
		print(inv)		
		result = addInv(inv_desc,notes)
		print(result.reason)

def addInvTran(inv_desc,amount,transaction_desc, transaction_date):
	url = host + "invs/0/inv_trans.json"
	payload = {"inv_tran":{"inv_desc":inv_desc,"amount":amount,"transaction_desc":transaction_desc,"transaction_date":transaction_date}}
	return postPayload(url,payload)

def updateInvTransAtRails():
	invs = tp_db_interface.getAssetsTable()
	for inv in invs:
		inv_desc = inv[0]


		print(">>>>>adding transaction for investment: " + inv_desc)
		#print(investment_desc)
		invTrans = tp_db_interface.getAssetTransactions(inv_desc)


		for tran in invTrans:
				amount = tran[0]
				transaction_desc = tran[1]
				transaction_date = tran[2]
				print("-----Investment: " + inv_desc)
				print("About to add investment transaction :"+transaction_desc +"; Amount: " + str(amount))
				result = addInvTran(inv_desc,amount,transaction_desc, transaction_date)
				print("Added attempted; result is: " + result.reason)






