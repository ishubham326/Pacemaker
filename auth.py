#!/usr/bin/env python3

import csv,sqlite3
from params import params as p

#Test Code to read csv file
class auth():
    def __init__(self):
        self.user = []
        self.pw = []
        self.t_list = []
        self.o_list = []
        self.max_users = False
        self.green = False#login
        self.line_count = 0
        self.reg = False #registered
        self.match = False #match betwen input and data
        self.currentUser = None

        with sqlite3.connect("UserDB.db") as db:
            cursor = db.cursor()
            cursor.execute('SELECT * FROM user')
            temptable = cursor.fetchall()
            #print(f'temptable')
            for row in temptable:
                if(self.max_users == False):
                    #print (f'Max_users == {max_users}, run = {line_count}')
                    if(self.line_count>=10):
                        self.max_users = True
                    #used to skip first line, titles of columns
                    self.user.insert(self.line_count,row[1])
                    self.pw.insert(self.line_count,row[2])
                    self.line_count += 1
            print(f'\nProcessed {self.line_count} lines\n')
        i=0
        while i<len(self.user):
            print (f' Passowrd for {self.user[i]} == {self.pw[i]}\n')
            i=i+1

    #run as soon as login is pressed
    def login_auth(self, user, password):
        self.green = False
        x=0
        propindex =  0
        while x<len(self.user):
            if(user == self.user[x]):
                propindex= x
                break;
            x=x+1
        print(f'\n \b Index at {x+1}')
        if(password == self.pw[propindex]):
            #print(f'\n{[propindex+1]}\n')
            print (f' \n  {self.user[propindex]} logged in!')
            self.currentUser = self.user[propindex]
            #self.currentUser = 'Sean'
            self.green=True
        else:
            print("Invalid Username or Password")
            #self.green=False;
        return self.green
        for key in params:
            randomdict["key"]


    def reg_auth(self, newUser, newPassword):
        j=0
        #self.match = False
        while j < len(self.user):
            if(newUser == self.user[j]):
                print("\nUsername already in database")
                self.match = True
                break;
            j=j+1
        if(self.line_count <10 and self.match == False):
            counter = 0
            with sqlite3.connect("UserDB.db") as db:
                cursor2 = db.cursor()
                insertNewUser = '''INSERT INTO user(username,password)
                VALUES(?,?)'''
                cursor2.execute(insertNewUser,[(newUser),(newPassword)])
                db.commit()
                self.line_count = self.line_count + 1
                self.user.insert(counter,newUser)
                self.pw.insert(counter,newPassword)
            print("Done Update")
            self.reg=True
            print(f'Registered! = {self.reg}')
        elif(self.line_count >= 10):
            print("Max users = 10. \n No Space")
            self.max_users = True
        print (f'{self.reg, self.max_users, self.match}')
        print(f'{self.line_count}')
        return (self.reg, self.max_users, self.match)

    def up_param(self):#30 colunms atm, skips first 3 (userid, suername, password)
        #expected format for input ( dont include quotation marks)

        #self.user[self.line_count-1] = 'Sean'
        # self.o_list = ['DDD',60]
        #self.t_list = ['VDD',70]
        # paramlist['mode'].set('DDD')
        # paramlist['lower_rate_limit'].set(100)
        #self.t_list.insert(paramlist)
        #print(f'{self.t_list[0]}, {self.user[self.line_count-1]}')
        #self.currentUser = 'Sean'

        with sqlite3.connect("UserDB.db") as db:
            c = db.cursor()
            for key in p:
                update = ("UPDATE user SET (%s) = ? WHERE (username = ? )" %(key))
                c.execute(update, [(p[key].get()),(self.currentUser)])
                db.commit()
            print(c.rowcount, "records(s) affected")
        return ("Done")

    def get_fetch(self):
    #    self.currentUser = 'Sean'
        return_dictionary = dict()
        keys = []
        values = []
        values_c = []

        with sqlite3.connect("UserDB.db") as db:
            c2 = db.cursor()
            fetchKey = ("SELECT * FROM user WHERE username = ?")
            c2.execute(fetchKey, [(self.currentUser)])
            columns = c2.description
            for i in range(len(columns)):
                if(i>2):
                    keys.insert(i,columns[i][0])

        #print(f'all keys:\n {keys}')
        #print(f'# of keys: {len(keys)}')

        with sqlite3.connect("UserDB.db") as db:
            c = db.cursor()
            values = []
            fetchValue = ("SELECT * FROM user WHERE username = ?")
            c2.execute(fetchValue, [(self.currentUser)])
            values = c2.fetchall()
            #print(f'{values[0]}')
        for j in range(31):
            if(j==30):
                break;
            else: values_c.append(values[0][j+3])

        #print(f'All values: \n{values_c}')
        #print(f'# of values: {len(values_c)}')

        for x in range(30):
            key = keys[x]
            value = values_c[x]
            return_dictionary[key] = value
            #print(f'\n{x}: \n{return_dictionary}')
        print(f'\nOuput: \n{return_dictionary}')
        return return_dictionary
####TO DO####
# - make var in login that stores username                  ✓
# - make dictionary in get_fetch() stores values from db    ✓

#Reg = True if regeistered
#max_users = True if max limit of 10 reached
#match = true if use already exists

#upFile("ran12dom", "1211")


# ##Login Runs
randomUser = "Sean"
randomPassword = "123131"

##Login Fails
# randomUser = "Ben"
# randomPassword = "001"
#
# #Registered
# newUser = "Raj11"
# newPassword = "12311"

#Reg - Already exists abs
# newUser = "Raj"
# newPassword = "10011"

# #login Runs
# randomUser = "Raj"
# randomPassword = "12311"


if __name__ == "__main__":
    start = auth()
    #start.upFile(someUser, somePassword)
    # start.reg_auth(newUser, newPassword)
    start.login_auth(randomUser,randomPassword)
    #start.up_param(p)
    start.get_fetch()
    #tempoutput = start.get_fetch()
    #print(f'{tempoutput}')
