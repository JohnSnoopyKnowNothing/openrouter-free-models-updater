# OpenRouter Free Models Updater

A tool to update Hermes Agent configuration with the latest free models from OpenRouter.

## Overview

This script fetches the current list of free models from OpenRouter's API and updates the Hermes configuration files to show only free models in the model picker (both CLI and Web UI).

## Prerequisites

- Python 3.7+
- [Hermes Agent](https://github.com/nousresearch/hermes-agent) installed and configured
- `requests` library (installed via requirements.txt)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/JohnSnoopyKnowNothing/openrouter-free-models-updater.git
   cd openrouter-free-models-updater
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the update script:

```bash
python3 update_openrouter_free_models.py
```

The script will:
1. Fetch free models from OpenRouter's frontend API
2. Update `~/.hermes/cache/model_catalog.json` (CLI model picker)
3. Update `~/.hermes-web-ui/cache/provider-model-catalog.json` (Web UI cache)
4. Display an update report

### After Running

**Important**: Refresh your browser (Ctrl+Shift+R) to see updated models in Web UI.

**Do NOT** run `hermes model --refresh` as it will overwrite the filtered list with all models (including paid ones).

## Configuration

The script uses the following default paths:

| File | Purpose |
|------|---------|
| `~/.hermes/cache/model_catalog.json` | CLI model picker |
| `~/.hermes-web-ui/cache/provider-model-catalog.json` | Web UI cache |

To customize these paths, edit the constants at the top of `update_openrouter_free_models.py`.

## How It Works

1. **API Endpoint**: Uses OpenRouter's frontend API which directly filters free models
   - Endpoint: `https://openrouter.ai/api/frontend/v1/models/find?active=true&fmt=cards&q=free`
   - This is more efficient than fetching all models and filtering by pricing

2. **Capability Detection**: Automatically detects model capabilities:
   - `reasoning`: Models with reasoning support
   - `vision`: Models with image/video input support
   - `tools`: Models with tool/function calling support

3. **Configuration Update**: Updates two JSON files that Hermes reads to populate model pickers

## Example Output

```
OpenRouter Free Models Updater
================================================================================
Fetching free models from: https://openrouter.ai/api/frontend/v1/models/find?active=true&fmt=cards&q=free
Found 25 models from API
Filtered to 19 free models with text output

Updating: /home/ubuntu/.hermes/cache/model_catalog.json
✓ Updated 19 models in model_catalog.json

Updating: /home/ubuntu/.hermes-web-ui/cache/provider-model-catalog.json
✓ Updated 19 models in provider-model-catalog.json

================================================================================
Update Report
================================================================================

Total free models: 19

Models:
   1. minimax/minimax-m3:free
      free, reasoning, vision, tools
   2. nvidia/nemotron-3-ultra-550b-a55b:free
      free, reasoning, tools
   ...

================================================================================

Next steps:
  1. Refresh your browser (Ctrl+Shift+R) to see updated models in Web UI
  2. Do NOT run `hermes model --refresh` as it will overwrite our filtered list
================================================================================

✓ Update completed successfully!
```

## Troubleshooting

### Script fails with "Error fetching API"
- Check your internet connection
- Verify OpenRouter API is accessible: `curl -I https://openrouter.ai/api/v1/models`

### Web UI still shows old models
- Hard refresh your browser: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
- Clear browser cache if needed

### CLI shows all models instead of free only
- Do NOT run `hermes model --refresh` - it overwrites the filtered list
- Verify `~/.hermes/cache/model_catalog.json` was updated correctly

## Automation (Optional)

### Cron Job

To automatically update free models daily:

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 3 AM)
0 3 * * * /usr/bin/python3 /path/to/update_openrouter_free_models.py >> /var/log/openrouter-update.log 2>&1
```


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [OpenRouter](https://openrouter.ai/) for providing the API
- [Hermes Agent](https://github.com/nousresearch/hermes-agent) for the model picker system

## Disclaimer

This tool is not officially affiliated with OpenRouter or Nous Research. Use at your own risk.
