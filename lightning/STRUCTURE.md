# Lightning Cog Structure


## Directory Structure

```
lightning/
├── __init__.py              # Package initialization
├── lightning.py             # Main cog file
├── README.md                # User documentation
├── SETUP.md                 # Quick start guide
└── services/
    ├── __init__.py          # Services package
    ├── base.py              # Base service class
    ├── blitzortung.py       # Blitzortung service
    ├── weatherapi.py        # WeatherAPI service
    └── openweathermap.py    # OpenWeatherMap service
```

## File Descriptions

### Main Cog
- **lightning.py** - Core cog with command handlers and configuration management
  - Minimal, focused on commands and routing
  - ~150 lines (down from ~400)
  - Easy to understand at a glance

### Services
- **base.py** - Abstract base class for all services
  - Defines the interface all services must implement
  - Handles aiohttp session management

- **blitzortung.py** - Blitzortung real-time lightning API
  - Fetches actual detected lightning strikes
  - Formats data for Discord display

- **weatherapi.py** - WeatherAPI.com service
  - Fetches weather-based lightning detection
  - Formats temperature, humidity, conditions
  - Requires free API key

- **openweathermap.py** - OpenWeatherMap service
  - Similar to WeatherAPI but different data format
  - Provides detailed weather information
  - Requires free API key

## Benefits of This Structure

✅ **Separation of Concerns** - Each service handles its own API logic  
✅ **Easy to Add Services** - Just extend `LightningService` base class  
✅ **Easier Testing** - Can test services independently  
✅ **Better Readability** - Smaller, focused files  
✅ **Easy Maintenance** - Changes to one service don't affect others  

## Adding a New Service

1. Create a new file in `services/` (e.g., `mynewapi.py`)
2. Import and extend `LightningService`
3. Implement `fetch()` and `display_data()` methods
4. Add to `services/__init__.py`
5. Add provider option in `lightning.py`

Example:
```python
# services/mynewapi.py
from .base import LightningService

class MyNewAPIService(LightningService):
    async def fetch(self, lat: float, lon: float, **kwargs) -> dict:
        # Your API logic here
        pass
    
    def format_display_name(self) -> str:
        return "My New API"
    
    def display_data(self, data: dict, location_name: str):
        # Return Discord embed
        pass
```
