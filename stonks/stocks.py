from discord import Embed, Color, Member, utils, File
from discord.ext import commands
from db import dbconn
from utils import cf_api, paginator
from random import randint
from datetime import datetime
from io import BytesIO
import asyncio
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import os


class Stocks(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.db = dbconn.DbConn()
        self.users = self.db.get_all_users()
        self.cf = cf_api.CodeforcesAPI()
        self.trading = 1

    def stock_value(self, rating):
        caps = [1200, 1400, 1600, 1900, 2100, 2300, 2400, 2600, 3000, 9999]
        rank = 0
        while rating >= caps[rank]:
            rank += 1
        return round(1.2**rank*rating/100, 2)

    def embed(self, text, color=None):
        color = Color(color) if color else Color(randint(0, 0xFFFFFF))
        return Embed(description=text, color=color)

    async def update_ratings(self, ctx):
        to_update = []
        for handle in self.db.get_all_handles():
            to_update += [handle]
            if len(to_update) == 5:
                ratings = await self.cf.get_ratings(to_update)
                for i in range(5):
                    self.db.update_rating(to_update[i], ratings[i])
                to_update = []
        if to_update:
            ratings = await self.cf.get_ratings(to_update)
            for i in range(len(ratings)):
                self.db.update_rating(to_update[i], ratings[i])
        await ctx.channel.send(embed=self.embed("Ratings have been updated."))

    @commands.command(brief='About the bot.')
    async def about(self, ctx):
        embed = Embed(title="About Stonks",
                      description="Stonks is a bot created by manish#9999 using "
                                  "[discord.py](https://discordpy.readthedocs.io/en/latest/index.html). The source "
                                  "code can be found [here](https://github.com/iammanish17/Stonks)!",
                      color=Color.dark_teal())
        embed.set_footer(text=f"Requested by {str(ctx.author)}", icon_url=ctx.author.avatar_url)
        await ctx.channel.send(embed=embed)

    @commands.command(brief='Register your Codeforces handle!')
    async def register(self, ctx, username: str):
        """Register your Codeforces handle!"""
        if ctx.author.id in self.users:
            await ctx.channel.send(embed=self.embed(ctx.author.mention+", Your handle is already registered."))
            return

        if ";" in username:
            await ctx.channel.send(embed=self.embed("Invalid Username!"))
            return

        if self.db.check_handle_exists(username):
            await ctx.channel.send(embed=self.embed("That handle is already associated with another account."))
            return

        is_valid_handle = await self.cf.check_handle(username)
        if not is_valid_handle[0]:
            await ctx.channel.send(embed=self.embed(is_valid_handle[1]))
            return

        code = "Stonks:VerificationCode-"+hex(randint(6969696969696969, 6969696969696969696969696969696969))[2:]
        link = "https://codeforces.com/settings/social"
        men = ctx.author.mention
        await ctx.channel.send("%s Please go to %s and change your First Name to `%s` to verify your account. "
                               "You have 1 minute. (You can reset it again after verification.)" % (men, link, code))
        await asyncio.sleep(60)
        if await self.cf.get_first_name(username) == code:
            rating = await self.cf.get_rating(username)
            self.db.create_profile(ctx.author.id, username, rating)
            self.users.add(ctx.author.id)
            await ctx.channel.send(embed=self.embed("✅ Your handle has been successfully set. To view your holdings,"
                                                    " type `+holdings`.", 0x00FF00))
        else:
            await ctx.channel.send(embed=self.embed("Time up! You did not verify your handle. Try again.", 0xFF0000))

    @commands.command(brief='See the latest trends of a stock!')
    async def trends(self, ctx, stock: str):
        """See the latest trends of a stock!"""
        is_valid = await self.cf.check_handle(stock)
        if ";" in stock or not is_valid[0]:
            await ctx.channel.send(embed=self.embed(ctx.author.mention+", Not a valid stock!"))
            return
        changes = await self.cf.get_rating_changes(stock)
        if not changes:
            await ctx.channel.send(embed=self.embed(ctx.author.mention+", No recent trends found."))
            return

        profit_symbol = ":arrow_up_small:"
        loss_symbol = ":small_red_triangle_down:"

        result = []
        for name, old, new, time in changes:
            oldvalue = self.stock_value(old)
            value = self.stock_value(new)
            symbol = profit_symbol if new >= old else loss_symbol
            percent = round(abs(oldvalue - value)/oldvalue*100, 2)
            result.append("**$%.2f** ⟶ **$%.2f** %s (%.2f%s)" % (oldvalue, value, symbol, percent, "%"))
        e = Embed(title="Recent trends for %s" % stock, description="\n".join(result), color=Color.dark_purple())
        e.set_footer(text="Requested by "+str(ctx.author), icon_url=ctx.author.avatar_url)
        await ctx.channel.send(embed=e)

    @commands.command(brief='View the current rating of a user!')
    async def rating(self, ctx, member: Member = None):
        """"View the current rating of any user!"""
        if not member:
            member = ctx.author
        handle = self.db.get_handle(member.id)
        if not handle:
            await ctx.channel.send(embed=self.embed("Handle for %s not found in database." % member.mention))
            return
        rating = self.db.get_rating(handle)

        embed = Embed(title="Rating info for %s" % handle, color=Color.blurple())
        embed.add_field(name="User", value=member.mention)
        embed.add_field(name="Handle", value=handle)
        embed.add_field(name="Rating", value=rating)
        await ctx.channel.send(embed=embed)

    @commands.command(brief='Shows info of a particular stock.')
    async def info(self, ctx, stock: str):
        """Shows the info of a particular stock!"""
        info = self.db.get_stock(stock)
        if len(info) == 0:
            await ctx.channel.send(embed=self.embed("No stock called '%s' found in database." % stock))
            return
        rating, maxrating = await self.cf.get_rating(stock), await self.cf.get_best_rating(stock)
        market = 0
        for owner, quantity in info:
            if owner == -1:
                market = quantity
        e = Embed(title="Stock info for %s" % stock, color=Color.dark_blue())
        e.add_field(name="Current Value", value="**$%.2f**" % self.stock_value(rating), inline=False)
        e.add_field(name="Max. Value", value="$%.2f" % self.stock_value(maxrating), inline=False)
        e.add_field(name="Available Stocks in market", value="%d" % market, inline=False)
        e.set_footer(text="Requested by "+str(ctx.author), icon_url=ctx.author.avatar_url)
        await ctx.channel.send(embed=e)

    @commands.cooldown(1, 1.5, commands.BucketType.guild)
    @commands.command(brief='Sell a stock.')
    async def sell(self, ctx, stock: str, amount: int):
        """Sell a particular stock!
            +sell <stock> <amount>"""
        if not self.trading:
            await ctx.channel.send(embed=self.embed("Trading has been disabled currently!"))
            return
        if ctx.author.id not in self.users:
            await ctx.channel.send(embed=self.embed("You need to set your handle using the `+register` command first."))
            return
        info = self.db.get_stock(stock)
        rating = await self.cf.get_rating(stock)
        money = self.db.get_balance(ctx.author.id)
        if len(info) == 0:
            await ctx.channel.send(embed=self.embed("No stock called '%s' found in database." % stock, 0xFF0000))
            return
        owned = 0
        market = 0
        for owner, quantity in info:
            if owner == ctx.author.id:
                owned = quantity
            if owner == -1:
                market = quantity
        if amount <= 0:
            await ctx.channel.send(embed=self.embed("You must sell at least 1 stock.", 0xFF0000))
            return
        if amount > owned:
            await ctx.channel.send(embed=self.embed("You cannot sell more stocks than you own.", 0xFF0000))
            return

        profit = self.stock_value(rating) * amount
        self.db.set_balance(ctx.author.id, money + profit)
        self.db.update_holding(ctx.author.id, stock, owned-amount)
        self.db.update_market(stock, market+amount)
        await ctx.channel.send(embed=self.embed(ctx.author.mention+", Successfully sold %d stocks of **%s** for $%.2f!"
                                                % (amount, stock, profit), 0x00FF00))

    @commands.cooldown(1, 1.5, commands.BucketType.guild)
    @commands.command(brief='Buy a stock.')
    async def buy(self, ctx, stock: str, amount: int):
        """Buy a particular stock!
            +buy <stock> <amount>"""
        if not self.trading:
            await ctx.channel.send(embed=self.embed("Trading has been disabled currently!"))
            return
        if ctx.author.id not in self.users:
            await ctx.channel.send(embed=self.embed("You need to set your handle using the `+register` command first."))
            return
        if amount <= 0:
            await ctx.channel.send(embed=self.embed("You must buy atleast 1 stock."))
            return
        info = self.db.get_stock(stock)
        rating = await self.cf.get_rating(stock)
        money = self.db.get_balance(ctx.author.id)
        if len(info) == 0:
            await ctx.channel.send(embed=self.embed("No stock called '%s' found in database." % stock, 0xFF0000))
            return
        market = 0
        owned = 0
        owns = False
        for owner, quantity in info:
            if owner == ctx.author.id:
                owns = True
                owned = quantity
            if owner == -1:
                market = quantity
        if amount > market:
            await ctx.channel.send(embed=self.embed("You cannot buy more stocks than avaiable in the market!"))
            return
        cost = amount * self.stock_value(rating)
        if cost > money:
            await ctx.channel.send(embed=self.embed("You do not have enough money to purchase %d stocks!" % amount))
            return
        self.db.set_balance(ctx.author.id, money - cost)
        if owns:
            self.db.update_holding(ctx.author.id, stock, owned + amount)
        else:
            self.db.create_holding(ctx.author.id, stock, owned + amount)
        self.db.update_market(stock, market - amount)

        await ctx.channel.send(
            embed=self.embed(ctx.author.mention + ", Successfully purchased %d stocks of **%s** for **$%.2f!**"
                                                  "\n\n Your new balance is **$%.2f**."
                             % (amount, stock, cost, money-cost), 0x00FF00))

    @commands.command(brief='See the list of available stocks!')
    async def market(self, ctx):
        """Shows the list of all available stocks!"""
        market_stocks = self.db.get_market_stocks()
        if len(market_stocks) == 0:
            await ctx.channel.send(embed=self.embed("No stocks found in market!"))
            return
        headers = ["#", "Stock", "Qt.", "Price"]
        count = 0
        data = []
        for stock, quantity in market_stocks:
            count += 1
            price = self.stock_value(self.db.get_rating(stock))
            data.append([str(count), stock, str(quantity), "$%.2f" % price])
        await paginator.Paginator(data, headers, "Available Stocks in Market").paginate(ctx, self.client)

    @commands.command(brief='See the list of stocks you own!')
    async def holdings(self, ctx, member: Member = None):
        """Lists the stocks owned by you or any other member.
            +holdings <member>"""
        if not member:
            member = ctx.author
        if member.id not in self.users:
            await ctx.channel.send(embed=self.embed("The user is not registered!"))
            return
        title = "Owned by "+str(member)
        stocks = self.db.get_user_stocks(member.id)
        if len(stocks) == 0:
            await ctx.channel.send(embed=self.embed("The user does not own any stocks."))
            return
        headers = ["#", "Stock", "Qt.", "Value"]
        count = 0
        data = []
        for stock, quantity in stocks:
            count += 1
            value = "$%.2f" % self.stock_value(self.db.get_rating(stock))
            data.append([str(count), stock, str(quantity), str(value)])
        await paginator.Paginator(data, headers, title).paginate(ctx, self.client)

    @commands.command(brief='View your balance!', aliases=['bal'])
    async def balance(self, ctx, member: Member = None):
        """Shows your balance!"""
        if not member:
            member = ctx.author
        if member.id not in self.users:
            await ctx.channel.send(embed=self.embed("The user is not registered!"))
            return
        money = self.db.get_balance(member.id)
        await ctx.channel.send(embed=self.embed(member.mention+" has a balance of **$%.2f**." % money))

    @commands.command(brief='Shows leaderboards ordered by net worth!')
    async def networth(self, ctx):
        """Shows the leaderboards ordered by net worths!"""
        worths = {}
        for stock, owner, quantity in self.db.get_all_holdings():
            if owner not in worths:
                worths[owner] = self.db.get_balance(owner)
            worths[owner] += quantity * self.stock_value(self.db.get_rating(stock))
        top = [sorted(worths.values(), reverse=True), sorted(worths, key=worths.get, reverse=True)]
        title = "Net Worth Leaderboards"
        headers = ["#", "User", "Worth"]
        count = 0
        data = []
        for i in range(len(top[0])):
            worth, owner = top[0][i], top[1][i]
            count += 1
            member = utils.get(ctx.guild.members, id=int(owner))
            data.append([str(count), member.name if member else self.db.get_handle(int(owner)), "$%.2f" % worth])
        await paginator.Paginator(data, headers, title).paginate(ctx, self.client)

    @commands.command(brief='Shows leaderboards ordered by money!')
    async def rich(self, ctx):
        """Shows the leaderboards ordered by balance!"""
        money = {}
        for user in self.users:
            money[user] = self.db.get_balance(user)
        top = [sorted(money.values(), reverse=True), sorted(money, key=money.get, reverse=True)]
        title = "Richest people in "+ctx.guild.name
        headers = ["#", "User", "Balance"]
        count = 0
        data = []
        for i in range(len(top[0])):
            money, owner = top[0][i], top[1][i]
            count += 1
            member = utils.get(ctx.guild.members, id=int(owner))
            data.append([str(count), member.name if member else self.db.get_handle(int(owner)), "$%.2f" % money])
        await paginator.Paginator(data, headers, title).paginate(ctx, self.client)

    @commands.command(brief='Update ratings for all users!')
    @commands.has_role('Admin')
    async def updateratings(self, ctx):
        """Updates ratings for all users after any contest (Admin-use only)!"""
        await ctx.channel.send(embed=self.embed("Updating ratings... Please wait."))
        await self.update_ratings(ctx)

    @commands.command(brief='Enable/disable trading!')
    @commands.has_role('Admin')
    async def trading(self, ctx, value: str):
        """Enable/disable trading (Admin-use only)!
            +trading <enable/disable>"""
        if value.lower() == "enable":
            await ctx.channel.send(embed=self.embed("Updating ratings first before enabling trading... Please wait."))
            await self.update_ratings(ctx)
            self.trading = 1
            await ctx.channel.send(embed=self.embed("Successfully enabled trading!"))
        elif value.lower() == "disable":
            self.trading = 0
            await ctx.channel.send(embed=self.embed("Successfully disabled trading!"))
        else:
            await ctx.channel.send(embed=self.embed("Invalid choice!", 0xFF0000))

    @commands.command(brief='Shows distribution of a particular stock!')
    async def distrib(self, ctx, stock):
        """Shows distribution of a particular stock!
            +distrib <stock>"""
        owner_list = self.db.get_owners(stock)
        if not owner_list:
            await ctx.channel.send(embed=self.embed("No stock called %s found in database." % stock))
            return
        owners, percentage, explode = [], [], []
        for owner_id, quantity in owner_list:
            if quantity == 0:
                continue
            owner = "market"
            if owner_id != -1:
                owner = utils.get(ctx.guild.members, id=owner_id)
                if owner:
                    owner = owner.name
                else:
                    owner = self.db.get_handle(owner_id)
            owners.append(owner)
            percentage.append(quantity)
            explode.append(0 if owner_id != ctx.author.id else 0.1)
        plt.pie(percentage,
                explode=explode,
                textprops={'color': "w", "fontsize": 14},
                labels=owners,
                shadow=True,
                autopct='%1.1f%%',
                startangle=140)
        plt.tight_layout()
        filename = "%s.png" % str(ctx.message.id)
        plt.savefig(filename, transparent=True)
        with open(filename, 'rb') as file:
            discord_file = File(BytesIO(file.read()), filename='plot.png')
        os.remove(filename)
        plt.clf()
        plt.close()
        embed = Embed(title="Distribution of stocks of %s" % stock, color=Color.blue())
        embed.set_image(url="attachment://plot.png")
        embed.set_footer(text="Requested by " + str(ctx.author), icon_url=ctx.author.avatar_url)
        await ctx.channel.send(embed=embed, file=discord_file)

    @commands.command(brief='Plots the recent variations in the price of the stock!')
    async def plot(self, ctx, stock):
        """Plots the prices attained by the stock recently!
            +plot <stock>"""
        changes = await self.cf.get_rating_changes(stock, False)
        if not changes:
            await ctx.channel.send(embed=self.embed(ctx.author.mention+", No recent changes in the stock."))
            return
        x_axis, y_axis = [], []
        for name, old, new, time in changes:
            x_axis.append(datetime.fromtimestamp(time))
            value = self.stock_value(new)
            y_axis.append(value)
        ends = [-100000, 14.40, 20.16, 27.64, 39.39, 52.25, 68.67, 85.99, 111.79, 154.79, 100000]
        colors = ['#CCCCCC', '#77FF77', '#77DDBB', '#AAAAFF', '#FF88FF', '#FFCC88', '#FFBB55', '#FF7777', '#FF3333',
                  '#AA0000']
        plt.plot(x_axis, y_axis, linestyle='-', marker='o', markersize=3, markerfacecolor='white', markeredgewidth=0.5)
        plt.gca().yaxis.set_major_formatter(FormatStrFormatter('$%d'))
        ymin, ymax = plt.gca().get_ylim()
        bgcolor = plt.gca().get_facecolor()
        for i in range(1, 11):
            plt.axhspan(ends[i - 1], ends[i], facecolor=colors[i - 1], alpha=0.8, edgecolor=bgcolor, linewidth=0.5)
        plt.gcf().autofmt_xdate()
        locs, labels = plt.xticks()
        for loc in locs:
            plt.axvline(loc, color=bgcolor, linewidth=0.5)
        plt.ylim(ymin, ymax+3)
        plt.legend(["%s ($%.2f)" % (stock, y_axis[0])], loc='upper left')
        filename = "%s.png" % str(ctx.message.id)
        plt.savefig(filename)
        with open(filename, 'rb') as file:
            discord_file = File(BytesIO(file.read()), filename='plot.png')
        os.remove(filename)
        plt.clf()
        plt.close()
        embed = Embed(title="Stock Price graph for %s" % stock, color=Color.blue())
        embed.set_image(url="attachment://plot.png")
        embed.set_footer(text="Requested by "+str(ctx.author), icon_url=ctx.author.avatar_url)
        await ctx.channel.send(embed=embed, file=discord_file)

    @commands.command(brief='Force register a member!')
    @commands.has_role('Admin')
    async def forceregister(self, ctx, member: Member, username: str):
        """Force register a member!"""
        if member.id in self.users:
            await ctx.channel.send(embed=self.embed(ctx.author.mention+", %s is already registered." % member.name))
            return

        if ";" in username:
            await ctx.channel.send(embed=self.embed("Invalid Username!"))
            return

        if self.db.check_handle_exists(username):
            await ctx.channel.send(embed=self.embed("That handle is already associated with another account."))
            return

        is_valid_handle = await self.cf.check_handle(username)
        if not is_valid_handle[0]:
            await ctx.channel.send(embed=self.embed(is_valid_handle[1]))
            return

        rating = await self.cf.get_rating(username)
        self.db.create_profile(member.id, username, rating)
        self.users.add(member.id)
        await ctx.channel.send(embed=self.embed("Successfully registered %s with the handle %s!" % (member.mention,
                                                                                                    username)))

    @commands.command(brief='Change a member\'s handle!')
    @commands.has_role('Admin')
    async def updateuser(self, ctx, member: Member, new: str):
        if member.id not in self.users:
            await ctx.channel.send(embed=self.embed("The user is not registered."))
            return

        is_valid_handle = await self.cf.check_handle(new)
        if not is_valid_handle[0]:
            await ctx.channel.send(embed=self.embed(is_valid_handle[1]))
            return

        old = self.db.get_handle(member.id)
        self.db.update_handle(member.id, old, new)
        rating = await self.cf.get_rating(new)
        self.db.update_rating(new, rating)
        await ctx.channel.send(embed=self.embed("Successfully updated %s's handle to %s." % (member.mention, new)))


def setup(client):
    client.add_cog(Stocks(client))
