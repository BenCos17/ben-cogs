WeirdImages:

A Red Discord bot cog for generating and manipulating weird images.

***Requirements:***

Python 3.6+
discord.py
redbot.core
Pillow

***Installation:***

To install the WeirdImages cog, use the following command in your Red Discord bot instance:

csharp
Copy code
[p]cog install weirdimages
Commands
weird
Generates a weird image with random shapes and colors, applies filters, and sends it to the chat.

Usage: [p]weird [size]

***Arguments:***

size: the size of the image (default: 500)
Cooldown: 15 seconds

cursed
Combines two images in a cursed way and sends the result to the chat.

Usage: [p]cursed [image1] [image2]

Arguments:

image1: the URL or attachment of the first image
image2: the URL or attachment of the second image
Cooldown: 15 seconds

Filters
The following filters can be applied to images generated by the weird command:

CONTOUR: Finds the edges in an image and enhances them
BLUR: Blurs the image
DETAIL: Enhances the details in an image
EDGE_ENHANCE: Enhances the edges in an image
EDGE_ENHANCE_MORE: Enhances the edges in an image more than EDGE_ENHANCE
EMBOSS: Applies an emboss effect to an image
FIND_EDGES: Finds the edges in an image
SHARPEN: Sharpens an image
SMOOTH: Smooths an image
SMOOTH_MORE: Smooths an image more than SMOOTH
Example
To generate a weird image with size 800, use the following command:

csharp
Copy code
[p]weird 800
To combine two images in a cursed way, use the following command:

bash
Copy code
[p]cursed https://example.com/image1.png https://example.com/image2.png
I hope this helps! Let me know if you have any questions or need further assistance.
