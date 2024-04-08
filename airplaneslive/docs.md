Airplaneslive Cog Documentation

Overview

The Airplaneslive cog provides commands to retrieve information about aircraft using the airplanes.live API and Planespotters.net API. 
This cog is coded to be used with Discord bot using the Red-DiscordBot framework and running on the 3.5.x version of redbot.

thank you to the airplanes.live server (https://discord.gg/adsb) and also many people in the redbot server (https://discord.gg/red) who helped me out with this cogs and also my cogs in general 

(If you use this please consider setting up a feed to the site as would improve coverage for everyone.



Installation


To use the Airplaneslive cog, follow these steps:

# [p] is your prefix


[p]repo add ben-cogs https://github.com/BenCos17/ben-cogs



    [p]load airplaneslive

Commands
1. aircraft

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
    Example: [p]aircraft type B737

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

j. aircraft_to_json

    Description: Get aircraft information in JSON format.
    Usage: [p]aircraft_to_json <aircraft_type>
    Example: [p]aircraft_to_json Boeing 737



k.  Alert Command Usage

The alert command in this bot allows you to set up alerts for specific aircraft and receive notifications when those aircraft are detected. Below is a guide on how to use the alert commands:

1. **Setting Up an Alert**

   To set up an alert for a specific aircraft:
   ```
   [p]aircraft set_alert [HEX_ID] #[CHANNEL]
   ```
   Replace `[HEX_ID]` with the hexadecimal identifier of the aircraft and `#[CHANNEL]` with the channel where you want to receive alerts.

2. **Listing Active Alerts**

   To see a list of all active alerts:
   ```
   [p]aircraft list_alerts
   ```
   This command will display a list of all active alerts, showing the aircraft hex IDs and the channels where alerts are set to be sent.

3. **Removing an Alert**

   If you no longer want to receive alerts for a specific aircraft:
   ```
   [p]aircraft remove_alert [HEX_ID]
   ```
   Replace `[HEX_ID]` with the hexadecimal identifier of the aircraft for which you want to remove the alert.


l. set_max_requests   
(bot owner only command) 

    Description: Set the maximum number of requests the bot can make to the airplanes.live api. (Restricted to bot owner)
    Usage: [p]set_max_requests <max_requests>
    Example: [p]set_max_requests 20
