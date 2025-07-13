# SkySearch - Aircraft Tracking Discord Bot Cog

A powerful, modular Discord bot cog for tracking aircraft and airport information using real-time data from airplanes.live and other aviation APIs.

## 🏗️ New Modular Structure

The codebase has been refactored into a clean, modular structure for better maintainability, readability, and collaboration:

```
skysearch/
├── __init__.py                 # Main cog setup
├── skysearch.py               # Main cog class and core functionality
├── data/
│   ├── __init__.py
│   └── icao_codes.py          # ICAO code sets and intelligence data
├── utils/
│   ├── __init__.py
│   ├── api.py                 # API management and HTTP client
│   ├── helpers.py             # Helper utilities and embed creation
│   └── export.py              # Export functionality (CSV, PDF, TXT, HTML)
└── commands/
    ├── __init__.py
    ├── aircraft.py            # Aircraft-related commands
    ├── airport.py             # Airport-related commands
    └── admin.py               # Admin and configuration commands
```

## 📦 Module Overview

### Core Modules

- **`skysearch.py`**: Main cog class that orchestrates all components
- **`__init__.py`**: Cog setup and bot integration

### Data Layer

- **`data/icao_codes.py`**: Contains all ICAO code sets for intelligence data:
  - Law enforcement aircraft
  - Military and government aircraft
  - Medical response aircraft
  - Suspicious aircraft
  - News/media aircraft
  - Balloons
  - Accident history
  - Conflict zone aircraft
  - Agricultural/utility aircraft

### Utility Layer

- **`utils/api.py`**: 
  - HTTP client management
  - API request handling
  - Error handling and rate limiting
  - Authentication management

- **`utils/helpers.py`**:
  - Aircraft photo fetching
  - Embed creation and formatting
  - Data processing utilities

- **`utils/export.py`**:
  - CSV export functionality
  - PDF export with proper formatting
  - TXT and HTML export options
  - File management and cleanup

### Command Layer

- **`commands/aircraft.py`**: All aircraft-related commands:
  - `icao` - Search by ICAO hex code
  - `callsign` - Search by flight callsign
  - `reg` - Search by registration
  - `type` - Search by aircraft type
  - `squawk` - Search by squawk code
  - `military` - View military aircraft
  - `ladd` - View LADD-restricted aircraft
  - `pia` - View private ICAO aircraft
  - `radius` - Search within radius
  - `closest` - Find closest aircraft
  - `export` - Export data to various formats
  - `scroll` - Scroll through aircraft

- **`commands/airport.py`**: All airport-related commands:
  - `info` - Airport information
  - `runway` - Runway details
  - `navaid` - Navigational aids
  - `forecast` - Weather forecasts

- **`commands/admin.py`**: Admin and configuration commands:
  - `alertchannel` - Set emergency alert channel
  - `alertrole` - Set emergency alert role
  - `autoicao` - Configure automatic ICAO lookup
  - `autodelete` - Configure auto-deletion of "not found" messages
  - `showalertchannel` - Show alert status
  - `setapikey` - Set API key (owner only)
  - `apikey` - Check API key status (owner only)
  - `clearapikey` - Clear API key (owner only)
  - `debugapi` - Debug API issues (owner only)

## 🚀 Benefits of the New Structure

### 1. **Maintainability**
- Clear separation of concerns
- Easy to locate and modify specific functionality
- Reduced code duplication
- Better error handling

### 2. **Readability**
- Logical organization by functionality
- Consistent naming conventions
- Clear module responsibilities
- Better documentation

### 3. **Collaboration**
- Multiple developers can work on different modules
- Reduced merge conflicts
- Clear ownership of code sections
- Easier code reviews

### 4. **Extensibility**
- Easy to add new command categories
- Simple to add new utility functions
- Modular API integration
- Flexible export formats

### 5. **Testing**
- Isolated components for unit testing
- Clear interfaces between modules
- Easier to mock dependencies
- Better test coverage

## 🔧 Setup and Installation

1. **Install Dependencies**:
   ```bash
   pip install discord.py aiohttp reportlab
   ```

2. **Configure API Keys**:
   - Set up airplanes.live API key: `[p]setapikey <your-api-key>`
   - Optional: Configure Google Maps API for airport imagery
   - Optional: Configure OpenAI API for airport summaries
   - Optional: Configure airportdb.io API for runway data

3. **Load the Cog**:
   ```bash
   [p]load skysearch
   ```

## 📋 Available Commands

### Aircraft Commands
- `[p]aircraft icao <hex>` - Search by ICAO hex code
- `[p]aircraft callsign <callsign>` - Search by flight callsign
- `[p]aircraft reg <registration>` - Search by registration
- `[p]aircraft type <type>` - Search by aircraft type
- `[p]aircraft squawk <code>` - Search by squawk code
- `[p]aircraft military` - View military aircraft
- `[p]aircraft ladd` - View LADD-restricted aircraft
- `[p]aircraft pia` - View private ICAO aircraft
- `[p]aircraft radius <lat> <lon> <radius>` - Search within radius
- `[p]aircraft closest <lat> <lon> [radius]` - Find closest aircraft
- `[p]aircraft export <type> <value> <format>` - Export data
- `[p]aircraft scroll` - Scroll through aircraft

### Airport Commands
- `[p]airport info <code>` - Get airport information
- `[p]airport runway <code>` - Get runway information
- `[p]airport navaid <code>` - Get navigational aids
- `[p]airport forecast <code>` - Get weather forecast

### Admin Commands
- `[p]aircraft alertchannel [#channel]` - Set alert channel
- `[p]aircraft alertrole [@role]` - Set alert role
- `[p]aircraft autoicao [true/false]` - Configure auto ICAO lookup
- `[p]aircraft autodelete [true/false]` - Configure auto-deletion
- `[p]aircraft showalertchannel` - Show alert status

### Owner Commands
- `[p]setapikey <key>` - Set airplanes.live API key
- `[p]apikey` - Check API key status
- `[p]clearapikey` - Clear API key
- `[p]debugapi` - Debug API issues

## 🔄 Migration from Old Structure

The new modular structure maintains full backward compatibility. All existing commands and functionality work exactly the same way. The only changes are internal organization and improved maintainability.

## 🤝 Contributing

When contributing to the codebase:

1. **Follow the modular structure** - Place new code in appropriate modules
2. **Use the utility classes** - Leverage existing helpers and API managers
3. **Maintain consistency** - Follow existing naming and formatting conventions
4. **Add documentation** - Document new functions and classes
5. **Test thoroughly** - Ensure new features work with existing functionality

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **airplanes.live** - Real-time aircraft data
- **planespotters.net** - Aircraft photography
- **airport-data.com** - Airport information
- **airportdb.io** - Runway and navaid data
- **Google Maps** - Mapping and imagery
- **OpenAI** - AI-powered summaries