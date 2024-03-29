Airplaneslive Cog Documentation
Overview

The Airplaneslive cog provides commands to retrieve information about aircraft using the airplanes.live API and Planespotters.net API. This cog is designed to be integrated into a Discord bot using the Red-DiscordBot framework.
Installation

To use the Airplaneslive cog, follow these steps:

    


[p]repo add ben-cogs https://github.com/BenCos17/ben-cogs



    [p]load airplaneslive

Commands
1. aircraft_group

    Description: This command group provides subcommands to retrieve information about aircraft based on different parameters.

Subcommands:
a. hex

    Description: Get information about an aircraft by its hexadecimal identifier.
    Usage: [p]aircraft hex <hex_id>
    Example: [p]aircraft hex ABC123

b. callsign

    Description: Get information about an aircraft by its callsign.
    Usage: [p]aircraft callsign <callsign>
    Example: [p]aircraft callsign DLH456

c. reg

    Description: Get information about an aircraft by its registration.
    Usage: [p]aircraft reg <registration>
    Example: [p]aircraft reg N12345

d. type

    Description: Get information about aircraft by its type.
    Usage: [p]aircraft type <aircraft_type>
    Example: [p]aircraft type Boeing 747

e. squawk

    Description: Get information about an aircraft by its squawk code.
    Usage: [p]aircraft squawk <squawk_value>
    Example: [p]aircraft squawk 7700

f. military

    Description: Get information about military aircraft.
    Usage: [p]aircraft military
    Example: [p]aircraft military

g. ladd

    Description: Limiting Aircraft Data Displayed (LADD).
    Usage: [p]aircraft ladd
    Example: [p]aircraft ladd

h. pia

    Description: Get information about privacy ICAO address.
    Usage: [p]aircraft pia
    Example: [p]aircraft pia

i. radius

    Description: Get information about aircraft within a specified radius of a location.
    Usage: [p]aircraft radius <lat> <lon> <radius>
    Example: [p]aircraft radius 51.5074 -0.1278 50

2. aircraft_to_json

    Description: Get aircraft information in JSON format.
    Usage: [p]aircraft_to_json <aircraft_type>
    Example: [p]aircraft_to_json Boeing 737

3. set_max_requests

    Description: Set the maximum number of requests the bot can make to the API. (Restricted to bot owner)
    Usage: [p]set_max_requests <max_requests>
    Example: [p]set_max_requests 20
