import os
import asyncio
import random
import interactions
from interactions import *
from dotenv import load_dotenv
from db import *
from datetime import datetime,timedelta
from interactions import SlashCommandOption,component_callback

# Load environment variables from .env files
load_dotenv()

# retrieve the DISCORD_TOKEN environment variable

TOKEN = os.getenv('DISCORD_TOKEN')
SERVER_ID = os.getenv('SERVER_ID')
OWNER_ID = os.getenv('OWNER_ID')
win_plus = int(os.getenv('win_plus'))


# Create bot instance
bot = Client(debug_scope=SERVER_ID, intents=Intents.ALL, token=TOKEN, send_command_tracebacks=False)


@slash_command(name="registration", description="Create New User )")
async def registration_function(ctx: SlashContext):
    
    user_id = ctx.author.id
    username = ctx.author.display_name
    join_date = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        
    res = create_new_user(user_id,username,join_date)
    if res :
        # "User created successfully!"
        embed = Embed(
            title="User Registration",
            description="New user registered successfully!",
            color=0x00ff00
            )
        embed.add_field(name="Username", value=username, inline=False)
        embed.add_field(name="Join Date", value=join_date, inline=False)
        
        # Sending the embed
        await ctx.send(embed=embed)

@slash_command(name="profile_view",description="View your user profile details")
async def profile(ctx: SlashContext):
    user_id = ctx.author.id
    username =  ctx.author.display_name
    
    user_data = find_user({"_id" :user_id })
    
    if user_data :
        balance = user_data.get("wallet", {}).get("balance", 0)
        transactions = user_data.get("wallet", {}).get("transaction_list", 0)
        
        # Create the embed
        embed = Embed(title=f"Profile for {username}", color=0x0000FF)
        
        embed.add_field(name="Balance", value=f"₹{balance}", inline=False)
        if transactions:
            transaction_list_str = ""
            for idx, transaction in enumerate(transactions, start=1):
                trans_amount = transaction[0].replace("IN", "").replace("OUT", "")
                trans_time = transaction[1]
                trans_type = transaction[2] 
                transaction_list_str += f"{idx}. Type: {trans_type}, Amount: ₹{trans_amount}, Time: {trans_time}\n"
            
            embed.add_field(name="Transaction History", value=transaction_list_str, inline=False)
        else:
            embed.add_field(name="Transaction History", value="No transactions yet", inline=False)
        
        await ctx.send(embed=embed)
    else:
        await ctx.send("User not found or data not available.")   


@slash_command(name="coin_game",description="Ye Sab Kismat Ka Khel Hai", options=[
    SlashCommandOption(
        name="user_choice",
        description="Please select 'Head' or 'Tail' If you win the game you will get 2x value back",
        type=OptionType.STRING,
        required=True,
        choices=[
            {"name": "Head", "value": "head"},
            {"name": "Tail", "value": "tail"}
        ]
    ),
     SlashCommandOption(
        name="amount",
        description="Enter the amount you want to bet",
        type=OptionType.INTEGER,
        required=True
    )
])
async def coin_game(ctx, user_choice: str, amount: int):
    
    user_id = ctx.author.id
    res = check_user_balance(user_id,amount)
    if res == True :
        current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        debit_user_balance(amount,user_id,current_time)
    elif res == "nouser" :
        await ctx.send("User not found. Please register.")
        return
    else :
        warning_message = "Your account balance is low. Please recharge your account."
        await ctx.send(content=warning_message)
        return
    
    # Generate a random result
    result = random.choice(["head", "tail"])
    print(result)
    
    if user_choice.lower() == result:
        embed = Embed(
        title="Game Result ",
        color=0x0000FF,
        thumbnail={
            "url": "https://cdn.discordapp.com/attachments/1230794909024391192/1234750071577247788/Head_Tail.jpeg?ex=6631de1d&is=66308c9d&hm=7316eb057b0991959aae31ec6d0d96408196e12cea00ce993e2ba6dbe5a59faa&",
            "width": 50,
            "height": 50,
        }
        )
        embed.add_field(name="Coin Toss Result", value=result.capitalize())
        embed.add_field(name="Outcome", value=f"You Win !")
        embed.add_field(name="Amount", value=f"{amount * win_plus} (will be returned in 1 hour)")
        # Send the embed to the user
        embed_ctx = await ctx.send(embed=embed)
        
        data = {
            "_id": embed_ctx.id,
            "game": "toss_game",
            # "bet": [user_id,user_choice,amount],
            "bet": [{"user_id" : user_id,"choise" : user_choice,"amount" : amount}],
        }
        res = store_result(data)
        if res :
            # winner_amount_return
            current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
            account_res = credit_user_balance(amount*win_plus,user_id,current_time)
            print(account_res)
            return
    else:
        embed = Embed(
        title="Game Result ",
        color=0x0000FF,
        thumbnail={
            "url": "https://cdn.discordapp.com/attachments/1230794909024391192/1234750071577247788/Head_Tail.jpeg?ex=6631de1d&is=66308c9d&hm=7316eb057b0991959aae31ec6d0d96408196e12cea00ce993e2ba6dbe5a59faa&",
            "width": 50,
            "height": 50,
        }
        )
        embed.add_field(name="Coin Toss Result", value=result.capitalize())
        embed.add_field(name="Outcome", value=f"You lose !")
        embed.add_field(name="Amount", value=f"You lose {amount} rupees !")
        embed.set_footer(text="Better luck next time!") 

        # Send the embed to the user
        embed_ctx = await ctx.send(embed=embed)

    
@slash_command(name="game_zone", description="Ye Sab Kismat Ka Khel Hai", options=[
    SlashCommandOption(
        name="game_type",
        description="Choose a game",
        type=OptionType.STRING,
        required=True,
        choices=[
            {"name": "Color-Game", "value": "color_game"}
        ]
    )
])
async def game_zone_function(ctx: SlashContext, game_type: str):
    user_id = ctx.author.id
    start_time = "2024-04-28 12:00"
    end_time = "2024-05-05 23:59"
    current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    
    if game_type == "color_game":
        event ="color_game"
        embed = Embed(title=f"Event : {event} ",
                    color=0x00ff00)
        
        embed.add_field(name="Start Time:", value=start_time, inline=False)
        embed.add_field(name="End Time:", value=end_time, inline=False)
        # Add footer
        embed.set_footer(text="Place your bet and click the corresponding button to make your guess!")
        
        component = [
            Button(style=ButtonStyle.RED, label="Red", custom_id="red"),
            Button(style=ButtonStyle.BLUE, label="Blue", custom_id="blue"),
            Button(style=ButtonStyle.GREY, label="Cyan", custom_id="cyan")
        ]
        
        res = find_user({"_id" : user_id})
        if res:
            # Sending the embed with buttons
            embed_ctx =  await ctx.send(embed=embed, components=component) 
        else:
            await ctx.send("User not found. Please register.")
            return
        try:
            res = create_new_data(embed_ctx.id, event,current_time)
        except Exception as e:
            print("An error occurred while creating new data.",e)
        

@component_callback("red")
async def red_function(ctx : ComponentContext) :
    embed_id = ctx.message_id
    user_id = ctx.author.id
    my_model = Modal(
        ShortText(
            label="Select Option :",
            custom_id="user_choise",
            value="red",
        ),
        ShortText(
            label="Enter Amount (₹) :",
            placeholder="Enter Amount Please",
            custom_id="amount",
            required=True,
        ),
        title="Color Game Add Your Balance :",
    )
    await ctx.send_modal(modal=my_model)
    try :
        modal_ctx = await ctx.bot.wait_for_modal(my_model, timeout=60)
    except asyncio.TimeoutError:
            await ctx.send("The interaction has expired.")
            return
    if modal_ctx is None:
        await modal_ctx.send("User didn't enter amount or canceled the modal.")
        return
    user_amount = modal_ctx.responses.get("amount")
    
    res = check_user_balance(user_amount,user_id)
    if res :
        game_data = find_game_data(embed_id)
        user_bet = {
            "user_id" : user_id,
            "choise" : "red",
            "amount" : int(user_amount)}
        
        game_data['bet'].append(user_bet)
        print("Update data ::->",game_data)
        res = update_data(game_data)
        if res :
            current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
            debit_user_balance(user_amount,user_id,current_time)
        print(f"user amount added successfully :{res}")
        await modal_ctx.send(f"<@{ctx.author.id}> Your bet add successfully")
    else :
        warning_message = "Your account balance is low. Please recharge your account."
        await modal_ctx.send(content=warning_message)
        return
    
@component_callback("blue")
async def blue_function(ctx : ComponentContext) :
    embed_id = ctx.message_id
    user_id = ctx.author.id
    my_model = Modal(
        ShortText(
            label="Select Option :",
            custom_id="user_choise",
            value="blue",
        ),
        ShortText(
            label="Enter Amount (₹) :",
            placeholder="Enter Amount Please",
            custom_id="amount",
            required=True,
        ),
        title="Color Game Add Your Balance :",
    )
    await ctx.send_modal(modal=my_model)
    try :
        modal_ctx = await ctx.bot.wait_for_modal(my_model, timeout=60)
    except asyncio.TimeoutError:
            await ctx.send("The interaction has expired.")
            return
    if modal_ctx is None:
        await ctx.send("User didn't enter amount or canceled the modal.")
        return
    user_amount = modal_ctx.responses.get("amount")
    
    res = check_user_balance(user_amount,user_id)
    if res :
        game_data = find_game_data(embed_id)
        user_bet = {
            "user_id" : ctx.author.id,
            "choise" : "blue",
            "amount" : int(user_amount)}
        
        game_data['bet'].append(user_bet)
        print("Update data ::",game_data)
        res = update_data(game_data)
        if res :
            current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
            debit_user_balance(user_amount,user_id,current_time)
        await modal_ctx.send(f"<@{ctx.author.id}> Your bet add successfully")
    else :
        warning_message = "Your account balance is low. Please recharge your account."
        await modal_ctx.send(content=warning_message)
        return

@component_callback("cyan")
async def cyan_function(ctx : ComponentContext) :
    embed_id = ctx.message_id
    user_id = ctx.author.id
    my_model = Modal(
        ShortText(
            label="Select Option :",
            custom_id="user_choise",
            value="cyan",
        ),
        ShortText(
            label="Enter Amount (₹) :",
            placeholder="Enter Amount Please",
            custom_id="amount",
            required=True,
        ),
        title="Color Game Add Your Balance :",
    )
    await ctx.send_modal(modal=my_model)
    try :
        modal_ctx = await ctx.bot.wait_for_modal(my_model, timeout=60)
    except asyncio.TimeoutError:
            await ctx.send("The interaction has expired.")
            return
    if modal_ctx is None :
        await ctx.send("User didn't enter amount or canceled the modal.")
        return
    user_amount = modal_ctx.responses.get("amount")
    res = check_user_balance(user_amount,user_id)
    if res :
        game_data = find_game_data(embed_id)
        user_bet = {
            "user_id" : user_id,
            "choise" : "cyan",
            "amount" : int(user_amount)}
        game_data['bet'].append(user_bet)
        res = update_data(game_data)
        if res :
            current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
            debit_user_balance(user_amount,user_id,current_time)
        await modal_ctx.send(f"<@{ctx.author.id}> Your bet add successfully")
    else :
        warning_message = "Your account balance is low. Please recharge your account."
        await modal_ctx.send(content=warning_message)
        return



@slash_command(name="create_result",description="Comming soon result",options=[
    SlashCommandOption(
        name="game_result",
        description="Choose a result game",
        type=OptionType.STRING,
        required=True,
        choices=[
            # {"name": "Head-Tail", "value": "toss_game"},
            {"name": "Color-Game", "value": "color_game"}
        ]
    )
])
async def create_result_function(ctx: SlashContext, game_result: str):
    
    if game_result:
        user_id = ctx.author.id
        if str(user_id) == OWNER_ID :
            result_res = generate_result(game_result)
        
            print("Result is:", result_res)
            await ctx.send("Result Create Successfully.")
        else :
            await ctx.send("Only admins can access it.")
    else:
        await ctx.send(content="No game result provided.")


@slash_command(name="show_result",description="Show the result of a game",options=[
    SlashCommandOption(
        name="show_result",
        description="Choose a game for result",
        type=OptionType.STRING,
        required=True,
        choices=[
            {"name": "Head-Tail", "value": "toss_game"},
            {"name": "Color-Game", "value": "color_game"}
        ]
    )
])
async def show_result_function(ctx : SlashContext,show_result : str) :
    
    if str(ctx.author.id) == OWNER_ID :
        result_data = all_result_data(show_result)
        print("RESULT ::->",result_data)
        if result_data is None or len(result_data) == 0 :
            await ctx.send("No Result available.")
            return
        
        embed = Embed(title="Top Game Results",color=0x0000FF)
        
        for index,data in enumerate(result_data,start=1) :
            event = data.get('game')
            user = data.get('bet')[0].get('user_id')
            choise = data.get('bet')[0].get('choise')
            amount = data.get('bet')[0].get('amount')
            
            embed.add_field(name="Winner", value=index, inline=True)
            embed.add_field(name="Event :", value=event, inline=True)
            embed.add_field(name="User :", value=f"<@{user}>", inline=True)
            embed.add_field(name="Choise :", value=choise, inline=False)
            embed.add_field(name="Amount :", value=amount, inline=False)
            
        await ctx.send(embeds=embed)
    else :
        await ctx.send("Only admins can access it.")


@slash_command(name="recharge",description="Recharge your account",options=[
    SlashCommandOption(
        name="amount",
        description="Enter the amount for recharge",
        type=OptionType.INTEGER,
        required=True
    )
])
async def recharge_function(ctx : SlashContext, amount : int) :
    user_id = ctx.author.id
    time = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    res = find_user({"_id" : user_id})
    if res:
        if amount:
            try:
                res = credit_user_balance(amount,user_id,time)
                if res :
                    await ctx.send("Account recharged successfully.")
                    return
                await ctx.send(res)
            except Exception as e:
                await ctx.send(f"An error occurred while recharging your account: {str(e)}")
        else :
            await ctx.send("Please enter the amount for recharge.")
    else:
        await ctx.send("User not found. Please register.")
        return




        

@Task.create(IntervalTrigger(minutes=1))
async def result_expiry_payment():
    result = all_result_data()
    
    for index,data in enumerate(result) :
        current_time = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        if current_time > data.get('expiry') :
            
            delete_result(data.get('_id'))
            
    print("It's been 30 minutes!")

    
@listen() 
async def on_ready():
    # This event is called when the bot is ready to respond to commands
    print("Ready")
    print(f"This bot is owned by {bot.owner}")
    result_expiry_payment.start()

# Start bot 
bot.start()

