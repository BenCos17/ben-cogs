# Lightning Cog - Multi-API Support Implementation

## What's Included

Your Lightning cog now supports **3 free APIs** for lightning tracking:

### 1. **Blitzortung** (Recommended - No API Key!)
- Real-time actual lightning strike detection
- Crowdsourced global network
- No authentication needed
- Best for: Real-time lightning observations
- Free: ✅ Yes

### 2. **WeatherAPI**
- Weather-based thunderstorm detection
- Forecast and current weather data
- Free tier: 1 million calls/month
- API Key: Required (free at weatherapi.com)
- Best for: Weather-integrated lightning info

### 3. **OpenWeatherMap**
- Weather-based thunderstorm detection  
- Detailed weather conditions
- Free tier: 1,000 calls/day
- API Key: Required (free at openweathermap.org)
- Best for: Detailed weather analysis

## Quick Start

### Without API Key (Blitzortung)
```
[p]lightning setprovider blitzortung
[p]lightning check 40.7128 -74.0060 "New York"
```

### With API Key (WeatherAPI)
```
[p]lightning setprovider weatherapi
[p]lightning setkey YOUR_API_KEY_HERE
[p]lightning check 40.7128 -74.0060 "New York"
```

### With API Key (OpenWeatherMap)
```
[p]lightning setprovider owm
[p]lightning setkey YOUR_API_KEY_HERE
[p]lightning check 40.7128 -74.0060 "New York"
```

## Core Commands

- `[p]lightning setprovider <provider>` - Switch between APIs
- `[p]lightning setkey <key>` - Set API key (not needed for Blitzortung)
- `[p]lightning check <lat> <lon> [label]` - Check for lightning
- `[p]lightning strike [intensity]` - Manual strike logging
- `[p]lightning stats [user]` - View statistics
- `[p]lightning log [limit]` - See recent strikes

## Features

✅ Real-time API calls  
✅ Multiple data sources  
✅ Strike history logging  
✅ User statistics tracking  
✅ Server leaderboards  
✅ Customizable intensity levels  
✅ Embeded error handling  

## Notes

- All APIs are free (with free tier limitations)
- Blitzortung is best for actual real-time lightning
- WeatherAPI and OpenWeatherMap are forecast-based
- Choose the provider that best suits your needs
