# Currency Cog Commands Documentation

The Currency Cog provides commands to convert currency and get exchange rates using the FreeCurrencyAPI. Below are the details of the commands available in this cog.

## Commands

### 1. `currency`

**Usage:**

[p]currency <amount> <from_currency> <to_currency>

markdown


**Description:**
Converts an amount from one currency to another using the latest exchange rates.

**Parameters:**
- `amount`: The amount of money to be converted (must be a floating-point number).
- `from_currency`: The currency code of the currency you want to convert from (e.g., `USD`, `EUR`).
- `to_currency`: The currency code of the currency you want to convert to (e.g., `USD`, `EUR`).

**Examples:**
- `[p]currency 100 USD EUR` - Converts 100 USD to EUR.

**Notes:**
- If the API key is not set, the bot will prompt you to set it using the command `[p]set api freecurrencyapi api_key,YOUR_API_KEY`.
- If invalid currency codes are provided, the bot will display a list of supported currencies.

### 2. `rates`

**Usage:**

[p]rates <base_currency>

markdown


**Description:**
Fetches the latest exchange rates for a given base currency.

**Parameters:**
- `base_currency`: The currency code of the base currency you want to get exchange rates for (e.g., `USD`, `EUR`).

**Examples:**
- `[p]rates USD` - Fetches the latest exchange rates for USD.

**Notes:**
- If the API key is not set, the bot will prompt you to set it using the command `[p]set api freecurrencyapi api_key,YOUR_API_KEY`.
- If an invalid base currency code is provided, the bot will display a list of supported currencies.
  

## Setting the API Key

Before using the commands, you need to set the API key for FreeCurrencyAPI, 
You will need to create an account with https://freecurrencyapi.com

**Command:**

[p]set api freecurrencyapi api_key,YOUR_API_KEY

markdown


**Parameters:**
- `YOUR_API_KEY`: Your API key for FreeCurrencyAPI.

**Example:**

[p]set api freecurrencyapi api_key,abc123xyz

vbnet


**Notes:**
- The API key is required for the commands to function correctly. If the API key is not set, the bot will notify you.

## Error Handling

The cog handles several errors gracefully and provides informative messages in the following cases:
- Invalid currency codes
- Missing or incorrect API key
- Network issues or API errors

Make sure to check the error messages and follow the instructions provided to resolve any issues.

---

For further assistance, please create a github issue [here](https://github.com/BenCos17/ben-cogs/issues/new)] or on discord at bencos18.
