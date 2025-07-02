from redbot.core import commands
import aiohttp
from bs4 import BeautifulSoup
import asyncio
from discord.errors import NotFound
import discord

# Define the maximum SCP number here
MAX_SCP_NUMBER = 8999  

class SCPListView(discord.ui.View):
    def __init__(self, pages, ctx, category):
        super().__init__(timeout=120)
        self.pages = pages
        self.ctx = ctx
        self.category = category
        self.current_page = 0
        self.total_pages = len(pages)
        self.message = None

    def make_embed(self):
        page = self.pages[self.current_page]
        desc = "\n".join([
            f"[{key.upper()}: {title}]({link})\n{desc}" for key, title, link, desc in page
        ])
        embed = discord.Embed(
            title=f"SCPs in category: {self.category if self.category else 'all'} (Page {self.current_page+1}/{self.total_pages})",
            description=desc,
            color=discord.Color.blue()
        )
        return embed

    async def update(self, interaction):
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    @discord.ui.button(emoji="⬅️", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You can't control this pagination.", ephemeral=True)
            return
        if self.current_page > 0:
            self.current_page -= 1
            await self.update(interaction)

    @discord.ui.button(emoji="➡️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You can't control this pagination.", ephemeral=True)
            return
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            await self.update(interaction)

    @discord.ui.button(emoji="🛑", style=discord.ButtonStyle.danger)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("You can't control this pagination.", ephemeral=True)
            return
        await interaction.response.edit_message(content="Listing cancelled by user.", embed=None, view=None)
        self.stop()

    async def on_timeout(self):
        if self.message:
            await self.message.edit(content="Pagination timed out.", embed=None, view=None)

class scpLookup(commands.Cog):
    """A cog for looking up SCP articles with more detailed information."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name='scp', invoke_without_command=True)
    async def scp_group(self, ctx, scp_number: str = None):
        """Main command for SCP lookups. Use `scp <subcommand>` for more options."""
        if scp_number is not None:
            await self.scp_lookup(ctx, scp_number)
        else:
            await ctx.send("Please specify a subcommand or SCP number. Available subcommands: lookup, list, random, info.")

    @scp_group.command(name='lookup')
    async def scp_lookup(self, ctx, scp_number: str, search_term: str = None):
        """Search SCP articles and provide a summary and number."""
        base_url = "https://scp-data.tedivm.com/data/scp/items/index.json"  # SCP Data API endpoint

        # Check if the input is a valid SCP number format
        if scp_number.lower().startswith("scp-"):
            # Fetch specific SCP article from the API
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url) as response:
                    if response.status == 200:
                        articles = await response.json()  # Await the JSON response
                        article_key = scp_number.lower()  # Normalize the SCP number for lookup

                        # Check if the specific SCP article exists in the API data
                        if article_key in articles:
                            article = articles[article_key]
                            title = article['title']
                            description = article.get('description', 'Description not available.')[:500]  # Limit to 500 characters
                            read_more_link = f"[Read more](https://scpwiki.com/{scp_number})"

                            # If a search term is provided, check if it's in the description
                            if search_term:
                                if search_term.lower() in description.lower():
                                    await ctx.send(f"**{title}**\nThe term '{search_term}' was found in {scp_number}.\n{description}\n{read_more_link}")
                                else:
                                    await ctx.send(f"**{title}**\nThe term '{search_term}' was not found in {scp_number}.\n{description}\n{read_more_link}")
                            else:
                                await ctx.send(f"**{title}**\n{description}\n{read_more_link}")
                        else:
                            await ctx.send(f"{scp_number} not found in the SCP Data API.")
                    else:
                        await ctx.send("Failed to fetch articles from the SCP Data API.")
        else:
            # If the input is not a valid SCP number, perform a search using the SCP Data API
            await ctx.send(f"Searching for articles containing '{scp_number}'...")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(base_url) as response:
                    if response.status == 200:
                        articles = await response.json()
                        found_articles = []

                        # Search through the articles for the term
                        for key, article in articles.items():
                            title = article['title']
                            content = article.get('raw_content', '')
                            
                            if scp_number.lower() in title.lower() or scp_number.lower() in content.lower():
                                found_articles.append(title)

                        if found_articles:
                            # Prepare the base message
                            base_message = f"Articles containing '{scp_number}':\n"
                            
                            # Create chunks of articles that fit within Discord's limit
                            current_chunk = base_message
                            for article in found_articles:
                                if len(current_chunk + article + "\n") > 1990:  # Using 1990 to be safe
                                    await ctx.send(current_chunk)
                                    current_chunk = article + "\n"
                                else:
                                    current_chunk += article + "\n"
                            
                            # Send the last chunk if it's not empty
                            if current_chunk:
                                await ctx.send(current_chunk)
                        else:
                            await ctx.send(f"No articles found containing: {scp_number}.")
                    else:
                        await ctx.send("Failed to fetch articles from the SCP Data API.")

    @scp_group.command(name='list')
    async def list_scp(self, ctx, category: str = None):
        """List SCP articles by category or a specific range."""
        base_url = "https://scp-data.tedivm.com/data/scp/items/index.json"  # Updated to use SCP Data API
        
        # Fetch SCP articles from the API
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url) as response:
                if response.status == 200:
                    articles = await response.json()  # Await the JSON response
                    article_titles = []
                    
                    # Filter articles by category if specified
                    for key, article in articles.items():
                        if category is None or category in article.get('tags', []):
                            article_titles.append(article['title'])

                    if not article_titles:
                        await ctx.send(f"No SCPs found in category: {category}.")
                        return

                    # PAGINATION if more than 50 results
                    if len(article_titles) > 50:
                        # Build a list of (key, title, link, desc) tuples
                        article_links = []
                        for key, article in articles.items():
                            if category is None or category in article.get('tags', []):
                                title = article['title']
                                link = f"https://scpwiki.com/{key}"
                                desc = article.get('description', 'No description available.').split('\n')[0][:100]
                                article_links.append((key, title, link, desc))

                        # Split into pages of 50
                        pages = [article_links[i:i+50] for i in range(0, len(article_links), 50)]
                        view = SCPListView(pages, ctx, category)
                        embed = view.make_embed()
                        view.message = await ctx.send(embed=embed, view=view)
                    else:
                        # If 50 or fewer, send as before
                        message = f"Listing SCPs in category: {category if category else 'all'}\n" + "\n".join([f"[{key.upper()}: {title}](https://scpwiki.com/{key})" for key, title, link in article_links])
                        await ctx.send(message)
                else:
                    await ctx.send("Failed to fetch SCP articles. Please try again later.")

    @scp_group.command(name='random')
    async def random_scp(self, ctx):
        """Fetch a random SCP article."""
        random_number = random.randint(1, 9999)  # scp range
        await self.scp_lookup(ctx, str(random_number))  # Reuse existing lookup command

    @scp_group.command(name='info')
    async def scp_info(self, ctx, scp_number: str):
        """Provide detailed information about an SCP."""
        url = f"http://www.scpwiki.com/scp-{scp_number}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:  # Set a timeout of 10 seconds
                    if response.status == 200:
                        page_content = await response.text()
                        soup = BeautifulSoup(page_content, 'html.parser')
                        
                        # Attempt to extract detailed information
                        title = soup.find('title').text if soup.find('title') else f"SCP-{scp_number}"
                        description_tag = soup.find('div', {'id': 'page-content'})
                        detailed_info = description_tag.text.strip() if description_tag else "Detailed information not available."

                        # Prepare the link
                        read_more_link = f"[Read more]({url})"
                        max_length = 1800 - len(title) - len(read_more_link) - 2  # Subtracting 2 for the newline characters

                        # Ensure max_length is positive
                        if max_length <= 0:
                            await ctx.send("The SCP title and link are too long to send any information, Working on this command still -Ben")
                            return

                        # Split the detailed_info into chunks of max_length
                        chunks = [detailed_info[i:i + max_length] for i in range(0, len(detailed_info), max_length)]
                        
                        # Send the first chunk
                        current_chunk = 0
                        message = await ctx.send(f"**{title}**\n{chunks[current_chunk]}\n{read_more_link}")
                        
                        # Add reactions in the correct order
                        if len(chunks) > 1:
                            await message.add_reaction("➡️")  # Add next chunk reaction first
                            await message.add_reaction("⬅️")  # Add previous chunk reaction second

                        # Handle reactions for navigation
                        def check(reaction, user):
                            return user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) in ["➡️", "⬅️"]

                        while True:
                            try:
                                reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                                
                                # Remove the user's reaction
                                await message.remove_reaction(reaction, user)

                                if str(reaction.emoji) == "➡️":
                                    if current_chunk < len(chunks) - 1:
                                        current_chunk += 1
                                        # Edit the original message with the new chunk
                                        await message.edit(content=f"**{title}**\n{chunks[current_chunk]}\n{read_more_link}")
                                    if current_chunk == len(chunks) - 1:
                                        await message.remove_reaction("➡️", user)  # Remove next reaction if at the last chunk
                                
                                elif str(reaction.emoji) == "⬅️":
                                    if current_chunk > 0:
                                        current_chunk -= 1
                                        # Edit the original message with the new chunk
                                        await message.edit(content=f"**{title}**\n{chunks[current_chunk]}\n{read_more_link}")
                                    if current_chunk == 0:
                                        await message.remove_reaction("⬅️", user)  # Remove previous reaction if at the first chunk

                            except asyncio.TimeoutError:
                                await ctx.send("You took too long to respond. Navigation timed out.")
                                break  # Exit the loop if the user doesn't react in time
                    else:
                        await ctx.send(f"SCP-{scp_number} not found. Status code: {response.status}")
        except aiohttp.ClientError as e:
            await ctx.send(f"An error occurred while fetching SCP-{scp_number}: {str(e)}")
        except Exception as e:
            await ctx.send(f"An unexpected error occurred: {str(e)}")

    @scp_group.command(name='search')
    async def scp_search(self, ctx, *, search_term: str):
        """Search for SCP articles by their name and within their content."""
        await ctx.send("Searching for articles may take a while, as this command uses web scraping and may break if the website structure changes. Please be patient...")

        # List of known SCP articles (SCP-001 to SCP-8999)
        scp_numbers = [f"SCP-{i:04}" for i in range(1, MAX_SCP_NUMBER + 1)]  # SCP-0001 to SCP-8999

        found_articles = []

        async with aiohttp.ClientSession() as session:
            for scp_number in scp_numbers:
                article_url = f"http://www.scpwiki.com/{scp_number}"
                try:
                    async with session.get(article_url) as response:
                        if response.status == 200:
                            article_content = await response.text()
                            soup = BeautifulSoup(article_content, 'html.parser')
                            content_div = soup.find('div', {'id': 'page-content'})
                            
                            if content_div:
                                content_text = content_div.get_text()
                                # Check if the search term is in the content or title
                                if search_term.lower() in content_text.lower() or search_term.lower() in scp_number.lower():
                                    found_articles.append(scp_number)
                        else:
                            continue  # Skip if the article does not exist
                except Exception as e:
                    await ctx.send(f"An error occurred while fetching {scp_number}: {str(e)}")

        if found_articles:
            await ctx.send(f"Articles containing '{search_term}':\n" + "\n".join(found_articles))
        else:
            await ctx.send(f"No articles found containing: {search_term}.")


