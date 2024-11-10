from redbot.core import commands
import aiohttp
from bs4 import BeautifulSoup
from discord.ui import View, Button

class SCPInfoView(View):
    def __init__(self, title, detailed_info, url):
        super().__init__(timeout=None)  # No timeout for the view
        self.title = title
        self.detailed_info = detailed_info
        self.url = url
        self.current_page = 0
        self.max_length = 4000
        self.pages = [detailed_info[i:i + self.max_length] for i in range(0, len(detailed_info), self.max_length)]

    async def send_page(self, interaction):
        if self.current_page < len(self.pages):
            await interaction.response.edit_message(content=f"**{self.title}**\n{self.pages[self.current_page]}\n[Read more]({self.url})", view=self)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous_button(self, button: Button, interaction):
        if self.current_page > 0:
            self.current_page -= 1
            await self.send_page(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(self, button: Button, interaction):
        if self.current_page < len(self.pages) - 1:
            self.current_page += 1
            await self.send_page(interaction)

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
    async def scp_lookup(self, ctx, scp_number: str):
        """Lookup SCP articles by their number and provide a summary."""
        url = f"http://www.scpwiki.com/scp-{scp_number}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    page_content = await response.text()
                    soup = BeautifulSoup(page_content, 'html.parser')
                    
                    # Attempt to extract the SCP title and description
                    title = soup.find('title').text if soup.find('title') else f"SCP-{scp_number}"
                    description_tag = soup.find('div', {'id': 'page-content'})
                    description = description_tag.text.strip()[:500] if description_tag else "Description not available."

                    await ctx.send(f"**{title}**\n{description}\n[Read more]({url})")
                else:
                    await ctx.send(f"SCP-{scp_number} not found.")

    @scp_group.command(name='list')
    async def list_scp(self, ctx, category: str = None):
        """List SCP articles by category or a specific range."""
        base_url = "https://scp-api.com/scp"
        
        # Determine the URL based on the category
        if category:
            url = f"{base_url}/category/{category}"
        else:
            url = base_url

        # Fetch SCP articles from the API
        response = requests.get(url)
        
        if response.status_code == 200:
            articles = response.json()
            if articles:
                article_titles = [article['title'] for article in articles]
                await ctx.send(f"Listing SCPs in category: {category if category else 'all'}\n" + "\n".join(article_titles))
            else:
                await ctx.send(f"No SCPs found in category: {category}.")
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

                        # Create a pagination view
                        view = SCPInfoView(title, detailed_info, url)
                        await ctx.send(content=f"**{title}**\n{view.pages[0]}\n[Read more]({url})", view=view)
                    else:
                        await ctx.send(f"SCP-{scp_number} not found. Status code: {response.status}")
        except aiohttp.ClientError as e:
            await ctx.send(f"An error occurred while fetching SCP-{scp_number}: {str(e)}")
        except Exception as e:
            await ctx.send(f"An unexpected error occurred: {str(e)}")


