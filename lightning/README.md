# Lightning Cog

A Redbot cog for tracking lightning strikes using multiple free APIs!

## Features

- **Multi-API Support**: Choose from 3 free lightning APIs
  - **Blitzortung**: Real-time crowdsourced lightning strikes (no API key needed!)
  - **WeatherAPI**: Weather-based lightning detection (free tier available)
  - **OpenWeatherMap**: Weather-based lightning data (free tier available)
- **Real-Time Checks**: Check for active lightning at any location
- **Manual Logging**: Record custom lightning strikes for fun/games
- **Statistics Tracking**: Track who triggered the most strikes
- **Leaderboards**: See top strikers in your server

## Installation


## API Setup

### Option 1: Blitzortung 
- **Best for**: Real-time actual lightning detection
- **Cost**: Free
- **API Key Required**: No
- Setup:
  ```
  [p]lightning setprovider blitzortung
  ```

  unfinished don't use ^

### Option 2: WeatherAPI (Free Tier Available)
- **Best for**: Simple weather-based lightning detection
- **Cost**: Free tier (1 million requests/month)
- **API Key Required**: Yes
- Setup:
  1. Get free API key at https://www.weatherapi.com/
  2. Run: `[p]lightning setprovider weatherapi`
  3. Run: `[p]lightning setkey YOUR_API_KEY`

### Option 3: OpenWeatherMap (Free Tier Available)
- **Best for**: Detailed weather data with thunderstorm info
- **Cost**: Free tier available (1,000 calls/day)
- **API Key Required**: Yes
- Setup:
  1. Get free API key at https://openweathermap.org/api
  2. Run: `[p]lightning setprovider owm`
  3. Run: `[p]lightning setkey YOUR_API_KEY`

## Commands

### Configuration
- `[p]lightning setprovider <weatherapi|owm|blitzortung>` - Choose your API provider (admin)
- `[p]lightning setkey <api_key>` - Set API key for current provider (admin)

### Checking Lightning
- `[p]lightning check <latitude> <longitude> [label]` - Check for lightning at a location

Examples:
```
[p]lightning check 40.7128 -74.0060                    # Check New York City
[p]lightning check 40.7128 -74.0060 NYC                # With a label
[p]lightning check 51.5074 -0.1278 London              # London, UK
```

### Manual Strike Logging
- `[p]lightning strike [intensity]` - Record a lightning strike (1-10 intensity)

### Statistics
- `[p]lightning stats [user]` - View your or another user's statistics
- `[p]lightning log [limit]` - View recent recorded strikes (1-50, default 10)
- `[p]lightning reset` - Clear all statistics (admin)

## Data Stored

**Per Guild:**
- Total strike count
- Strike history log (user, intensity, timestamp)
- Last strike timestamp
- API provider and key (encrypted by Redbot)

**Per User:**
- Number of strikes triggered by this user

## Examples

```
# Set up Blitzortung (easiest - no key!)
[p]lightning setprovider blitzortung
[p]lightning check 40.7128 -74.0060 "Times Square"

# Set up WeatherAPI
[p]lightning setprovider weatherapi
[p]lightning setkey YOUR_WEATHERAPI_KEY
[p]lightning check 35.6762 139.6503 "Tokyo"

# Have fun with manual strikes
[p]lightning strike 9
[p]lightning strike 5
[p]lightning stats @user
```

## API Comparison

| Feature | Blitzortung | WeatherAPI | OpenWeatherMap |
|---------|-----------|-----------|-----------------|
| Real-time strikes | ✅ Yes | ⚠️ Forecast only | ⚠️ Forecast only |
| API Key Required | ✅ yes | ✅ Yes | ✅ Yes |
| Free Tier | ⚠️ needs caching on server end and a feed  | ✅ 1M/month | ✅ 1000/day |
| Coverage | Global | Global | Global |
| Data Type | Actual strikes | Weather forecast | Weather data |
