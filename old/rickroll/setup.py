from setuptools import setup

setup(
    name="redbot-rickroll",
    version="0.1",
    author="Your Name",
    packages=["rickroll"],
package_data={"rickroll": ["data/rickroll_incoming.mp3"]},
    install_requires=["discord.py", "youtube_dl"],
    description="A Red Discord Bot cog that rickrolls users in voice channels.",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
