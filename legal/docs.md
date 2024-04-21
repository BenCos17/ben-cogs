Legal Cog Documentation

Overview

The Legal cog provides commands to generate legal documents such as subpoenas, court orders, and detailed court verdicts. This cog is designed for use with Discord bots running on the Red-DiscordBot framework.

Installation

To use the Legal cog, follow these steps:

1. Add the repository containing the Legal cog to your instance of Red-DiscordBot using the following command:
[p]repo add ben-cogs https://github.com/BenCos17/ben-cogs

2. Install the Legal cog with the following command:

[p]cog install ben-cogs legal

3. Load the Legal cog into your bot with the following command:

[p]load legal

Commands

1. subpoena

    Description: Generates a subpoena document.
    Usage: [p]subpoena <target_name>
    Example: [p]subpoena JohnDoe

2. courtorder

    Description: Generates a court order document.
    Usage: [p]courtorder <target_name> <action> <date> <signature>
    Example: [p]courtorder JaneDoe "Cease and Desist" "2023-01-01" "Judge Judy"

3. courtverdict

    Description: Generates a detailed and realistic court verdict.
    Usage: [p]courtverdict <case_number> <target_name> <verdict> <summary> <date> <judge_name> <charges...>
    Example: [p]courtverdict 12345 JohnDoe "Guilty" "Found guilty of all charges." "2023-01-01" "Judge Judy" "Theft" "Fraud"





