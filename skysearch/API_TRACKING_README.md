# 🚁 SkySearch API Request Tracking

This document explains how to use the new API request tracking functionality in SkySearch, which monitors all requests made to the airplanes.live API.

## 📊 Overview

The API request tracking system automatically monitors:
- **Total request count** and success rates
- **API mode usage** (primary vs fallback)
- **Endpoint-specific statistics** (hex lookup, callsign lookup, etc.)
- **Performance metrics** (response times, hourly/daily patterns)
- **Error tracking** (rate limits, auth failures, permission denied)
- **Time-based analytics** (last 24 hours, hourly breakdowns)

## 🔧 How It Works

### Automatic Tracking
Every API request made through `api.make_request()` is automatically tracked:
- Request success/failure status
- Response time measurement
- API mode used (primary or fallback)
- Endpoint categorization
- Timestamp recording

### Real-time Statistics
Statistics are updated in real-time and can be accessed through:
- Discord commands (`skysearch apistats`)
- Dashboard web interface (`/dashboard/apistats`)
- Programmatic access (`api.get_request_stats()`)

## 📱 Discord Commands

### View API Statistics
```
skysearch apistats
```
Shows a comprehensive embed with:
- Overall request counts and success rates
- API mode usage breakdown
- Performance metrics
- Top endpoints by usage
- Error details (if any)

### Reset Statistics
```
skysearch apistats_reset
```
Resets all API statistics to zero (**bot owner only**)

### Manual Save
```
skysearch apistats_save
```
Manually saves current API statistics to config (**bot owner only**)

### View Save Configuration
```
skysearch apistats_config
```
View the current automatic saving configuration (**bot owner only**)

## 🌐 Dashboard Integration

Access API statistics through the web dashboard at:
```
/dashboard/apistats
```

Features:
- **Grid layout** with organized statistics
- **Real-time updates** from the cog
- **Visual indicators** for different metric types
- **Error highlighting** with warning colors
- **Responsive design** for different screen sizes

## 💻 Programmatic Access

### Get Current Statistics
```python
# Get comprehensive API statistics
api_stats = cog.api.get_request_stats()

# Access specific metrics
total_requests = api_stats['total_requests']
success_rate = api_stats['success_rate']
avg_response_time = api_stats['avg_response_time']
```

### Available Statistics
```python
{
    'total_requests': 1234,                    # Total API requests made
    'successful_requests': 1200,               # Successful requests
    'failed_requests': 34,                     # Failed requests
    'rate_limited_requests': 5,                # Rate limit hits (429)
    'auth_failed_requests': 2,                 # Authentication failures (401)
    'permission_denied_requests': 1,           # Permission denied (403)
    'success_rate': 97.2,                      # Success rate percentage
    'api_mode_usage': {                        # API mode breakdown
        'primary': 1000,
        'fallback': 234
    },
    'endpoint_usage': {                        # Endpoint-specific counts
        'hex_lookup': 500,
        'callsign_lookup': 300,
        'registration_lookup': 200,
        'type_lookup': 150,
        'military_filter': 84
    },
    'hourly_requests': {                       # Hourly request counts
        1234567890: 50,                        # Unix timestamp hour -> count
        1234567891: 45
    },
    'daily_requests': {                        # Daily request counts
        1234567890: 1200                       # Unix timestamp day -> count
    },
    'requests_last_24h': 1200,                # Requests in last 24 hours
    'last_request_time': 1234567890.123,      # Unix timestamp of last request
    'last_request_time_formatted': '2024-01-15 14:30:45',
    'total_response_time': 45.67,             # Total response time in seconds
    'avg_response_time': 0.037                # Average response time per request
}
```

### Reset Statistics
```python
# Reset all statistics to zero
cog.api.reset_request_stats()
```

## 🔍 Endpoint Categorization

The system automatically categorizes requests into logical groups:

| Endpoint | Description | Example URLs |
|-----------|-------------|--------------|
| `hex_lookup` | ICAO hex code searches | `/?find_hex=A12345` |
| `callsign_lookup` | Flight callsign searches | `/?find_callsign=UAL123` |
| `registration_lookup` | Aircraft registration searches | `/?find_reg=N12345` |
| `type_lookup` | Aircraft type searches | `/?find_type=B738` |
| `squawk_filter` | Squawk code filtering | `/?filter_squawk=7700` |
| `military_filter` | Military aircraft filtering | `/?filter_mil` |
| `ladd_filter` | LADD-restricted aircraft | `/?filter_ladd` |
| `pia_filter` | Private ICAO addresses | `/?filter_pia` |
| `stats` | API statistics endpoint | `/stats` |
| `v2_endpoint` | V2 API endpoints | `/v2/hex/A12345` |

## 📈 Performance Monitoring

### Response Time Tracking
- **Automatic measurement** of request/response cycles
- **Running average** calculation
- **Performance degradation** detection

### Time-based Analytics
- **Hourly breakdowns** for traffic patterns
- **Daily aggregations** for trend analysis
- **Last 24 hours** rolling window

### Error Rate Monitoring
- **Success rate** percentage calculation
- **Error type** categorization
- **Rate limit** tracking for API quota management

## 🚨 Error Tracking

### HTTP Status Code Monitoring
- **401 Unauthorized**: API key authentication failures
- **403 Forbidden**: Permission denied for endpoints
- **429 Too Many Requests**: Rate limit exceeded
- **Other errors**: Network failures, timeouts, etc.

### Circuit Breaker Integration
The system works alongside existing error handling:
- **Automatic fallback** between primary/fallback APIs
- **Error counting** for health monitoring
- **Performance degradation** detection

## 🔧 Configuration

### Security & Permissions
- **View Statistics**: Available to all users (transparency)
- **Reset Statistics**: Bot owner only (prevents data loss)
- **Manual Save**: Bot owner only (prevents abuse)
- **Dashboard Access**: Available to all users with dashboard access

### No Additional Setup Required
The tracking system is **enabled by default** and requires no configuration:
- Automatically tracks all API requests
- No performance impact on normal operations
- Statistics persist across cog reloads

### Data Persistence
- **Red-DiscordBot Config**: Statistics are automatically saved to Red's config system
- **Survives Reloads**: All data persists when the cog is reloaded
- **Smart Auto-Saving**: Uses hybrid approach to prevent config spam:
  - Save every **10 requests** OR
  - Save every **30 seconds**
  - Whichever comes first
- **Manual Save**: Use `skysearch apistats_save` to manually save current stats
- **Config Monitoring**: Use `skysearch apistats_config` to view save settings

### Memory Usage
- **Minimal overhead**: ~1KB per 1000 requests
- **Automatic cleanup**: Old hourly/daily data is automatically managed
- **Efficient storage**: Uses defaultdict for sparse data

## 📊 Use Cases

### Bot Administrators
- **Monitor API usage** and rate limits
- **Track performance** and response times
- **Identify popular** endpoints and usage patterns
- **Debug issues** with specific API calls

### Developers
- **Performance optimization** based on real usage data
- **API quota management** and planning
- **Error rate monitoring** and alerting
- **Usage analytics** for feature development

### Users
- **Transparency** into API performance
- **Understanding** of system reliability
- **Monitoring** of service health

### Manual Testing
1. **Make API requests** through normal SkySearch commands
2. **Check statistics** with `skysearch apistats`
3. **Verify tracking** in dashboard interface
4. **Test reset** functionality with `skysearch apistats_reset`

## 🔮 Future Enhancements

### Planned Features
- **Export functionality** for statistics (CSV, JSON)
- **Historical data** storage and retrieval
- **Alerting system** for high error rates
- **API quota** monitoring and warnings
- **Performance benchmarking** against historical data

### Integration Opportunities
- **Discord webhooks** for statistics updates
- **External monitoring** systems (Grafana, etc.)
- **Logging integration** for detailed request logs
- **Analytics dashboard** with charts and graphs

## 📝 Technical Details

### Implementation
- **Thread-safe**: Uses asyncio locks for concurrent access
- **Memory efficient**: Minimal memory footprint
- **Fast access**: O(1) lookup for most operations
- **Serializable**: All data can be converted to JSON

### Data Persistence
- **Red-DiscordBot Config**: Statistics are stored in Red's config system
- **Automatic persistence**: Data survives cog reloads and bot restarts
- **Reset capability**: Manual reset clears all data
- **Lightweight design**: Uses Red's built-in data storage

### Performance Impact
- **Negligible overhead**: <1ms per request
- **Efficient updates**: Optimized data structures
- **Minimal memory**: Automatic cleanup of old data

## 🤝 Contributing

### Adding New Metrics
To add new tracking metrics:

1. **Update `_request_stats`** in `APIManager.__init__()`
2. **Modify `_update_request_stats()`** to track new data
3. **Update `get_request_stats()`** to include new metrics
4. **Add display logic** in Discord commands and dashboard

### Example Addition
```python
# Add new metric
self._request_stats['new_metric'] = 0

# Update in tracking
def _update_request_stats(self, ...):
    # ... existing code ...
    self._request_stats['new_metric'] += 1

# Include in output
def get_request_stats(self):
    stats = self._request_stats.copy()
    stats['new_metric'] = self._request_stats['new_metric']
    return stats
```

## 📞 Support

For questions or issues with API tracking:
1. **Check the logs** for error messages
2. **Verify cog loading** with `skysearch apistats`
3. **Test basic functionality** with the test script
4. **Report bugs** with detailed error information

---

**SkySearch API Request Tracking** - Providing comprehensive insights into your airplanes.live API usage! 🚁📊
