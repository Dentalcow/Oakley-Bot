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
@commands.has_role('Host') # Require user to have "Host" role to run this command
async def question(ctx, question_text: str, *options):
    global questions
    global host
    questions.append({
        'question': question_text,
        'options': list(options)
    })
    host = ctx.author
    await ctx.send(f"Question added: {question_text} ({', '.join(options)})")

# join command for players to join the game
@bot.slash_command(name='join')
async def join(ctx):
    global players
    if ctx.author not in players.values():
        players[len(players)+1] = ctx.author
        await ctx.send(f"{ctx.author.mention} joined the game.")

@bot.slash_command(name='list_players')
async def list_players(ctx):
    global players
    if(len(players) == 0):
        await ctx.send('No Players')
    else:
        player_list = "Players:\n"
        for i, player in players.items():
            player_list += f"{i}. {player.display_name}\n"
        await ctx.send(player_list)

@bot.slash_command(name='become_host')
async def become_host(ctx):
    global host

    # Check if the host role is already assigned
    if any(role.name == 'Host' for role in ctx.author.roles):
        await ctx.send(f"{ctx.author.mention}, you are already the host!")
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

    # Remove Host role from current host
    await host.remove_roles(ctx.guild.get_role(int(os.getenv('HOST_ROLE_ID'))))

    # Kick all players
    for player in players.values():
        await player.kick(reason="Game ended by host.")

    # Reset global variables
    host = None
    players = {}
    answers = {}

    await ctx.send("Game ended. All players have been kicked.")

@bot.slash_command(name='end_game')
@commands.has_role('Host')  # Require user to have "Host" role to run this command
async def end(ctx):
    global host
    global players
    global answers

    # Remove Host role from current host
    await host.remove_roles(ctx.guild.get_role(int(os.getenv('HOST_ROLE_ID'))))

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
@commands.has_role('Host') # Require user to have "Host" role to run this command
async def start(ctx):
    global questions
    global host
    global players
    global answers

    if host != ctx.author:
        await ctx.send("Only the host can start the game.")
        return

    if not questions:
        await ctx.send("No questions have been added yet.")
        return

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
            msg += f"{i+1}. {question['options'][i]}\n"
        msg += "\n*Type /answer <number> to choose your answer.*"
        await ctx.send(msg)

        # wait for answers
        for player in players.values():
            if player not in answers:
                def check(msg):
                    return msg.author == player and msg.content.isdigit() and int(msg.content) <= len(question['options'])
                answer = await bot.wait_for('message', check=check)
                answers[player] = question['options'][int(answer.content)-1]
                await answer.add_reaction('✅')

    # display results
    results = "**Results:**\n"
    for player in players.values():
        results += f"{player.display_name}: {answers.get(player, 'No answer')}\n"
    await ctx.send(results)

# start the bot
bot.run(os.getenv('TOKEN'))
