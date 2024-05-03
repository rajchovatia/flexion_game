import os
from pymongo.errors import PyMongoError,DuplicateKeyError
from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv
from helper.secure import custom_hasher
from helper.transaction import balance_in,balance_out
from datetime import datetime,timedelta
# Load environment Variables
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI, server_api=ServerApi("1"))

try:
    # Ping the MongoDB server
    client.admin.command("ping")
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)
    
# Connect Database and Collection Name 
db = client.satta_game
user_collection = db.user_data
game_data = db.game_data
game_result = db.game_result


def find_user(data) :
    try:
        results = user_collection.find_one(data)
        return results
    except PyMongoError as e:
        print("An error occurred while retrieving data:", e)
        return None
    

def create_new_user(user_id,username,join_date) :
    data = {
        "_id" : user_id,
        "username" : username,
        "join_date" : join_date,
        "wallet": {
        "balance": 1000,
        "transaction_list": []
        }   
    }
    try:
        existing_user = user_collection.find_one({"_id": user_id})
        if existing_user:
            return False
        else:
            user_collection.insert_one(data)
            return True
    except PyMongoError as e:
        print("An error occurred while retrieving data:", e)
        return str(e)


def create_new_data(embed_id,event,current_time) :
    data = {
    "_id": embed_id,
    "game": event,
    "time": current_time,
    "bet": []
}
    try :
        # Insert data into MongoDB
        result = game_data.insert_one(data)
        print("Data inserted with ID:", result.inserted_id)
    except DuplicateKeyError:
        print("Embed ID already exists in the database.")
    
    
def find_game_data(embed_id) :
    try:
        results = game_data.find_one(embed_id)
        return results
    except PyMongoError as e:
        print("An error occurred while retrieving data:", e)
        return None
    
    
def update_data(data):
    try:
        existing_data = game_data.find_one({"_id": data["_id"]})
        if existing_data:
            game_data.update_one({"_id": data["_id"]}, {"$set": data})
        else:
            return False
        return True
    except Exception as e:
        print(f"Error storing data: {e}")
        return False
    

def check_user_balance(user_id,amount=None) :
    try :
        result = user_collection.find_one({"_id" : user_id})
        if result is not None :
            wallet = result.get("wallet")
            print("user balance is :",wallet['balance'])
            if int(amount) > wallet['balance'] :
                return False
            else :
                return True
        else :
            return "nouser"
    except PyMongoError as e :
        return e
    
def credit_user_balance(amount,user_id,time=None) :
    try :
        user_details = user_collection.find_one({"_id": user_id})
        transaction = balance_in(amount)
        entry = [transaction,time,"credit"]
        if user_details :
            current_balance = user_details.get('wallet', {}).get('balance', 0)
            new_balance = max(current_balance + int(amount), 0)
            # Update the user's balance in the database
            user_collection.update_one(
                {"_id": user_id},
                {
                    "$set": {"wallet.balance": new_balance},
                    "$push": {"wallet.transaction_list": entry}
                }
            )
            return "User Balance Update Successfully"
        else:
                return "User not found !!"
    except PyMongoError as e:
        return str(e)
        
def debit_user_balance(amount,user_id,time=None) :
    try:
        user_document = user_collection.find_one({"_id": user_id})
        transaction = balance_out(amount)
        entry = [transaction,time,"debit"]
        if user_document:
            current_balance = user_document.get('wallet', {}).get('balance', 0)
            # Calculate the new balance
            new_balance = max(current_balance - int(amount), 0)
            # Update the user's balance in the database
            user_collection.update_one(
                {"_id": user_id},
                {
                    "$set": {"wallet.balance": new_balance},
                    "$push": {"wallet.transaction_list": entry}
                }
            )
            return "User Balance Update Successfully"
        else:
            return "User not found !!"
    except PyMongoError as e:
        return str(e)



def check_user_admin1(user_id) :
    
    user = find_user({"_id" : user_id})
    if user :
        if user['is_admin'] :
            return True
        else :
            return "You are not authorized to perform this action. Only admins can access it."
    else :
        return "User not found. Please contact the administrator for assistance."
    
    
def store_result(winner):
    # Calculate the expiry time
    expiry_time = (datetime.utcnow() + timedelta(minutes=60)).strftime("%Y-%m-%d %H:%M")
        
    try:
        data = {
            "_id": winner.get('_id'),
            "game": winner.get('game'),
            "bet": winner.get('bet'),
            "expiry" :expiry_time,
        }
        game_result.insert_one(data)
        print("Result stored successfully:")
        return True
    except Exception as e:
        print("An error occurred while storing the result:", e)

def generate_result(game):
    try:
        result = list(game_data.find({'game': game}).sort('bet.amount', -1))
        print("Generate Result is :->",result)
        if result :
            max_amount_choice = result[0]['bet'][0]['choise']
            for data in result:
                try:
                    if data.get("bet") and data["bet"]: 
                        if data["bet"][0].get("choise") is not None:
                            if max_amount_choice == data["bet"][0].get("choise") :
                                print("WIN:", data)
                                store_result(data)
                                user_id = data["bet"][0].get("user_id")
                                print("User_id is",user_id)
                                amount = data["bet"][0].get("amount")
                                print("AMOUNT ::->",amount)
                                expiry_time = (datetime.utcnow() + timedelta(minutes=60)).strftime("%Y-%m-%d %H:%M")
                                credit_user_balance(amount,user_id,expiry_time)
                        else:
                            pass
                    else:
                        pass
                except IndexError:
                    print("IndexError: 'bet' index out of range in data:")
            delete_game_data(game)
            return max_amount_choice
        else :
            return "No records found for game " + game
    except Exception as e:
        print("An error occurred:", e)


def delete_game_data(game_name):
    try:
        result = game_data.delete_many({'game': game_name})
        print("Deleted", result.deleted_count,)
    except Exception as e:
        print("An error occurred while deleting records:", e)

def delete_result(embed_id) :
    try:
        # Delete the document with the given embed_id
        result = game_result.delete_one({"_id": embed_id})
        
        if result.deleted_count > 0:
            print("Entry deleted successfully")
            return True
        else:
            print("No matching entry found for deletion")
            return False
    except Exception as e:
        print("An error occurred:", str(e))
        return False


def all_result_data(game=None):
    try:
        if game:
            result_list = list(game_result.find({"game": game}))
        else:
            result_list = list(game_result.find())
        return result_list
    except Exception as e:
        print("An error occurred while retrieving data:", e)
        return []
    

def recharge_account(user_id,amount) :
    user_data = user_collection.find_one({"_id" : user_id})
     # Check if user exists
    if user_data:
        current_balance = user_data.get("wallet", {}).get("balance", 0)
        new_balance = current_balance + amount
        user_collection.update_one({"_id": user_id}, {"$set": {"wallet.balance": new_balance}})

        print("New balance:", new_balance)
        return True
    else:
        return "User not found,Please register."
    
    