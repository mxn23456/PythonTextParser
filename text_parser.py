import re,sqlite3

#what is the purpose of this assignment?
# make an Quick parser to the note so that it adds the total of each vehicle next to it. Then sum up the amount 
# and add to the final book.


#-------PREPROCESS DOCUMENT------------------------------------
def removeBadChar(text):
	text=text.replace("\xc2\xa0"," ")
	return text

#require: isinstance(oldFileName,str) and 
#	isinstance(newFileName,str)
def removeDollarSign(oldFileName,newFileName):
	old = open(oldFileName,"r")
	new = open(newFileName,"a")
	line = old.readline()
	while line != '':
		line = line.replace("$","")
		new.write(line)
		line = old.readline()

#require: isinstance(oldFileName,str) and 
#	isinstance(newFileName,str)
def removeStarSign(oldFileName,newFileName):
	old = open(oldFileName,"r")
	new = open(newFileName,"a")
	line = old.readline()
	while line != '':
		line = line.replace("*","")
		new.write(line)
		line = old.readline()

def getLines(fileName):
	f=open(fileName,"r")
	return f.readlines()
#---------------END PREPROCESSING----------------------------------

#---------------ADDING TRANSACTIONS FOR A VEHILCE-------------------------
def getValue(line):
	num = 0
	if isATransaction(line):
		words=line.split()
		num = int(words[0])
	return num

def isATransaction(line):
	regex=re.compile("^(-|\+)[\d]+\s")
	res = regex.match(line)
	if res:
		return True
	else:
		return False

#require: isinstance(begin,int)
#	isinstance(end,int)
#	isinstance(lines,list)
def addLineValues(begin, end, lines):
	result = 0
	while begin <= end : 
		result = result + getValue(lines[begin])
		#print("result: " + str(result))
		begin = begin + 1
	return result


#require: isinstance(begin,int)
#	isinstance(end,int)
#	isinstance(lines,list)
#Note: assumed end line index covers the last transaction for the last vehicle in the range of indexes
#Note: this method is not used for closed deals. 
def getSubtotals(begin, end, lines):
	currentIndex = begin
	#beginOfAotherVehicleIndex = end
	while currentIndex < end:
		if lines[currentIndex].find('--') == 0:
			beginOfCurrentVehicleIndex = currentIndex
			beginOfAnotherVehicleIndex = beginOfCurrentVehicleIndex + 1
			while beginOfAnotherVehicleIndex < end: #continue down the index to find the next of vehicle
				if lines[beginOfAnotherVehicleIndex].find('--') == 0: # found next vehicle
					break
				beginOfAnotherVehicleIndex = beginOfAnotherVehicleIndex + 1
			subtotal = addLineValues(beginOfCurrentVehicleIndex + 1,beginOfAnotherVehicleIndex - 1, lines)
			lines = writeSubtotalNextToVeh(subtotal,beginOfCurrentVehicleIndex,lines)
			print("Adding subtotal: "+lines[beginOfCurrentVehicleIndex])
			currentIndex = beginOfAnotherVehicleIndex	
		else:
			currentIndex = currentIndex + 1
	return lines
			
def writeSubtotalNextToVeh(subtotal,beginOfCurrentVehicleIndex,lines):
	#print ("begin to write " + str(subtotal) + " to vehicle: "+lines[beginOfCurrentVehicleIndex])
	regex = re.compile("\((\+|-)*\d*\)")
	result = regex.search(lines[beginOfCurrentVehicleIndex])
	if subtotal > 0:
		subtotal = "(+"+str(subtotal)+")"
	else:
		subtotal = "("+str(subtotal)+")"
	if result:
		lines[beginOfCurrentVehicleIndex] = re.sub(regex.pattern,subtotal,lines[beginOfCurrentVehicleIndex])
	else:
		temp = lines[beginOfCurrentVehicleIndex].split('\n')
		lines[beginOfCurrentVehicleIndex] = temp[0] + subtotal + '\n'
	#print("line after writing: " + lines[beginOfCurrentVehicleIndex])
	return lines

#-----------END ADDING TRANSACTIONS FOR A VEHILCE------------------------

#-----------ADDING VEHICLES FOR A GROUP
def addGroupSubtotals(begin,end,lines):
	i=begin
	result=0
	while i<=end:
		if lineHasSubtotal(lines[i]):
			#print("adding line: " + lines[i])
			result = result + getSubtotal(lines[i])
		i=i+1
	return result
			

def lineHasSubtotal(line):
	regex=re.compile("^-{2,}.*\(\s*(-|\+)\d+\s*\)")
	res = regex.match(line)
	if res:
		return True
	else:
		return False
	
def getSubtotal(line):
	pattern = re.compile("\((\+|-)\d+\)")
	res=pattern.search(line)
	result=0
	if res is not None:
		result=int((res.group().replace("(","")).replace(")",""))
	return result

#require: end is the index of end of month's statement
def parseMonthlyStatement(begin,end,lines):
	#is this a group, get group total and display. If anything else like month, year, or note display to screen. Also, display the group name 
	#identify section, get subtotal, add subtotals, display each subtotal, display final calculation for that subtotal
	i=begin
	groupTotal=0
	beginOfGroup=re.compile("^(\/{2,})(\-{2,}).+$")
	endOfMonthlyStatement=re.compile("^>{2,}$")
	while i<=end:
		if beginOfGroup.search(lines[i]):  #Note: use match or search?
			#print("enter begin of group")
			beginningOfGroupIndex=i
			print()
			print("*****Begin adding group: "+lines[beginningOfGroupIndex])
			beginningOfAnotherGroupIndex=beginningOfGroupIndex+1
			while beginningOfAnotherGroupIndex < end: #Note: use match or search?
				#print("enter this loop")
				if beginOfGroup.search(lines[beginningOfAnotherGroupIndex]) or endOfMonthlyStatement.search(lines[beginningOfAnotherGroupIndex]):
				#if beginOfGroup.search(lines[beginningOfAnotherGroupIndex]):
					break
				beginningOfAnotherGroupIndex = beginningOfAnotherGroupIndex + 1
			#print("----beginning of Group index: " + str(beginningOfGroupIndex) + "; another group index: " + str(beginningOfAnotherGroupIndex))
			lines=getSubtotals(beginningOfGroupIndex,beginningOfAnotherGroupIndex,lines)
			subtotals = addGroupSubtotals(beginningOfGroupIndex + 1, beginningOfAnotherGroupIndex - 1, lines)
			lines = writeSubtotalsNextToGroup(subtotals,beginningOfGroupIndex,lines)
			i=beginningOfAnotherGroupIndex 
		else:
			if lines[i] != '\n':
				print(lines[i])
				#print()
			i = i + 1
	return lines
			
	
def writeSubtotalsNextToGroup(subtotals,beginningOfGroupIndex,lines): 
#note about this method: very similar to writeSubtotalNextToVeh. The only 
#	difference is the naming for subtotals and beginningOfGroupIndex
	#print ("begin to write " + str(subtotals) + " to group: "+lines[beginningOfGroupIndex])
	regex = re.compile("\((\+|-)*\d*\)")
	result = regex.search(lines[beginningOfGroupIndex])
	if subtotals > 0:
		subtotals = "(+"+str(subtotals)+")"
	else:
		subtotals = "("+str(subtotals)+")"
	if result:
		lines[beginningOfGroupIndex] = re.sub(regex.pattern,subtotals,lines[beginningOfGroupIndex])
	else:
		temp = lines[beginningOfGroupIndex].split('\n')
		lines[beginningOfGroupIndex] = temp[0] + subtotals + '\n'
	print("****line after writing: " + lines[beginningOfGroupIndex])
	return lines		

#-----------END ADDING VEHICLES FOR A GROUP

#------------BEGIN DATABASE WORK
def setUpDatabase (dbName):
	try:
		conn =sqlite3.connect(dbName)
		c= conn.cursor()
		c.executescript("""
			DROP TABLE IF EXISTS vehicle_transactions;
			DROP TABLE IF EXISTS vehicles;
			CREATE TABLE vehicle_transactions(id INT,amount INT,date TEXT, vehicle_id INT);
			CREATE TABLE vehicles(id INT,make TEXT, model TEXT,year INT, color TEXT, date_purchased TEXT, date_sold TEXT, vin TEXT, notes BLOB, pictures BLOB);""")
		conn.commit()
	except sqlite3.Error:
		if conn:
			conn.rollback()
			print ("There was an error with the SQL")
	finally:
		if conn:
			conn.close()

def addVehicle (make,model,year,color,date_purchased,date_sold,vin,notes,pictures):
	if vehicleExisted(make,model,year,color) == False:
		try:
			conn =sqlite3.connect(dbName)
			c= conn.cursor()
			c.executescript("INSERT INTO vehicles VALUES(?,?,?,?,?,?,?,?					)",make,model,year,color,date_purchased,date_sold,vin,notes,pictures)			
			conn.commit()
		except sqlite3.Error:
			if conn:
				conn.rollback()
				print ("There was an error with the SQL")
		finally:
			if conn:
				conn.close()

def vehicleExisted(make,model,year,color):
	conn =sqlite3.connect(dbName)
	c= conn.cursor()
	c.execute("SELECT * FROM vehicles WHERE make=?,model=?,year=?,color=?",make,model,year,color)
	result = c.fetchone()			
	conn.close()
	if result:
		return True
	else:	
		return False
	
	







#require: assume begin to end is within a month
#def parseUnclosedDeals(begin,end,lines):
#	regex = re.compile("\/+-*[a-zA-Z\s-]*\/+")
#	while begin<end:
#		match = regex.search(lines[begin]
#		begin += 1

#Note: same condition as the getSubtotal method
#def getTotal(begin,end,lines):

#new idea for version 2: put cars into tuples and prepare for database. for now, just make a quick way to calculate cost
#idea: identify whether a line is a transaction or a note. transaction should have the format "+ or - with number and space afterward". If it is a transaction, make sure it falls into the one before it

#desire functions:
# -remove more than 2 new lines
# -Convert closed deals to current convention by removing the 'profit' entry

#challenges need meet :
#1) convert -num/num to an integer value. How this this challenge solved individually? search for unclosed deals, do the math, then resolve each vehicle at a time all the way down untill it is in the closed deal
#2) having to parse unclosed deals. The reason is that the amount written next to the vehicles is a replication of profit, not the sum of all transaction within that vehicle. How is this challenge solved temporaryly? manuall identify the boundaries between unclosed and closed deals

#regex to note:
#  getting the month: "(January|February|March|April|May|June|July|August|September|October|November|December)"
# beginning of a group: "^(\/{2,})(\-{2,}).+$"
# unclosed deals group: "/^(\/{2,})(\-{2,})(unclosed)/i"
# the subtotal at the end of the line: "\((\+|-)\d+\)"
		
			
			
	

		
		
		
