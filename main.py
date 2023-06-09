import os
import requests
import json
import random
import disnake
from disnake.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = disnake.Intents.all()

bot = commands.Bot(command_prefix='/', intents=intents)

# Define global variables
questions = []
host = None
players = {}
answers = {}


# question command for host user to generate questions
@bot.slash_command(name='question')
@commands.has_role('Host')  # Require user to have "Host" role to run this command
async def question(ctx, question_text: str, options):
    global questions
    global host
    questions.append({
        'question': question_text,
        'options': list(options)
    })
    host = ctx.author
    await ctx.send(f"Question added: {question_text} ({', '.join(options)})")


@bot.slash_command(name='answer')
async def answer(ctx, answer_number: int):
    global players
    global questions
    global answers

    if ctx.author not in players.values():
        await ctx.send(f"{ctx.author.mention}, you're not a player in this game!")
        return

    if len(questions) == 0:
        await ctx.send("No questions have been added yet.")
        return

    if answer_number < 1 or answer_number > len(questions[0]['options']):
        await ctx.send(f"{ctx.author.mention}, please choose a number between 1 and {len(questions[0]['options'])}!")
        return

    player_number = list(players.keys())[list(players.values()).index(ctx.author)]
    answers[player_number] = answer_number - 1
    await ctx.send(f"{ctx.author.mention} chose option {answer_number}.")


# join command for players to join the game
@bot.slash_command(name='join')
async def join(ctx):
    global players
    # make sure that the player is not already in the game or is the host
    if ctx.author not in players.values() and ctx.author != host:
        players[len(players) + 1] = ctx.author
        await ctx.send(f"{ctx.author.mention} joined the game.")


# command to check if the host variable matches the host in discord
@bot.slash_command(name='check_host')
async def check_host(ctx):
    global host
    if host is not None:
        # check if the host variable matches host in discord and if not change the host to be the same as local variable
        host_role = disnake.utils.get(ctx.guild.roles, name='Host')
        if host_role.members:
            if host_role.members[0] != host:
                await host.remove_roles(ctx.guild.get_role(int(os.getenv('HOST_ROLE_ID'))))
                await host_role.members[0].add_roles(ctx.guild.get_role(int(os.getenv('HOST_ROLE_ID'))))
                host = host_role.members[0]
                await ctx.send(f"{host.display_name} is now the host.")
            else:
                await ctx.send(f"{host.display_name} is the host.")
    else:
        # check if somebody has the host role in discord and remove it
        host_role = disnake.utils.get(ctx.guild.roles, name='Host')
        if host_role.members:
            await host_role.members[0].remove_roles(host_role)
        await ctx.send("No host.")


@bot.slash_command(name='list_players')
@commands.has_role('Host')
async def list_players(ctx):
    global players
    if (len(players) == 0):
        await ctx.send('No Players')
    else:
        player_list = "Players:\n"
        for i, player in players.items():
            player_list += f"{i}. {player.display_name}\n"
        await ctx.send(player_list)


@bot.slash_command(name='become_host')
async def become_host(ctx):
    global host
    host_role = disnake.utils.get(ctx.guild.roles, name='Host')
    if any(role.name == 'Host' for role in ctx.author.roles):
        await ctx.send(f"{ctx.author.mention}, you are already the host!")
        return

    if host_role.members:
        if host_role.members[0] != host:
            await ctx.send(f"Error with host role. Please run /check_host command to re-align host role.")
            return

    # Check if the host role is empty and assign it to the user if it is
    host_role = disnake.utils.get(ctx.guild.roles, name='Host')
    if not host_role.members:
        await ctx.author.add_roles(host_role)
        host = ctx.author
        await ctx.send(f"{ctx.author.mention} is now the host!")
    else:
        await ctx.send("Sorry, the host role is already assigned to someone else.")


@bot.slash_command(name='end_game')
@commands.has_role('Host')  # Require user to have "Host" role to run this command
async def end(ctx):
    global host
    global players
    global answers

    host_role = disnake.utils.get(ctx.guild.roles, name='Host')

    # Remove host role from host
    await host.remove_roles(host_role)
    # Kick all players
    for player in players.values():
        await player.kick(reason="Game ended by host.")

    # Reset global variables
    host = None
    players = {}
    answers = {}

    await ctx.send("Game ended. All players have been kicked.")


# start command for the host to start the game
@bot.slash_command(name='start')
@commands.has_role('Host')  # Require user to have "Host" role to run this command
async def start(ctx, defaults: bool = False):
    global questions
    global host
    global players
    global answers

    if host != ctx.author:
        await ctx.send("Only the host can start the game.")
        return

    if defaults:
        # Create a dictionary of questions and options by sending a get request to
        # https://the-trivia-api.com/api/questions
        response = requests.get('https://the-trivia-api.com/api/questions', params={'amount': 10})
        print(response.json().question)
        print(response.json().correctAnswer)
        print(response.json().incorrectAnswers)


    elif not questions:
        await ctx.send("No questions have been added yet.")
        return
    else:
        # shuffle questions
        random.shuffle(questions)

        # reset answers
        answers = {}

        # ask questions
        for question in questions:
            # shuffle options
            random.shuffle(question['options'])

            # ask question
            msg = f"**Question:** {question['question']}\n"
            for i in range(len(question['options'])):
                msg += f"{i + 1}. {question['options'][i]}\n"
            msg += "\n*Type /answer <number> to choose your answer.*"
            await ctx.send(msg)

            # wait for answers
            for player in players.values():
                if player not in answers:
                    def check(msg):
                        return msg.author == player and msg.content.isdigit() and int(msg.content) <= len(
                            question['options'])

                    answer = await bot.wait_for('message', check=check)
                    answers[player] = question['options'][int(answer.content) - 1]
                    await answer.add_reaction('✅')

    # display results
    results = "**Results:**\n"
    for player in players.values():
        results += f"{player.display_name}: {answers.get(player, 'No answer')}\n"
    await ctx.send(results)


@bot.event
async def on_disconnect():
    global host

    if host is not None:
        host_role = disnake.utils.get(host.guild.roles, name='Host')
        await host.remove_roles(host_role)
        host = None


# start the bot
bot.run(os.getenv('TOKEN'))
