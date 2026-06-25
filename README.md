# Crypto-Bank-App
Level 6 Software Engineering & Agile Project

## Deployment

Use the deployment scripts in the deployment folder to start and stop the full application on Windows.

### Start the app

From the project root:

```powershell
cd deployment
.\start.bat
```

This will:
- create a Python virtual environment if needed
- install the backend dependencies
- start the Flask backend on port 5000
- start the React frontend on a free port (usually 3000 or the next available port)
- open the app in your default browser
- write logs to deployment/logs

### Stop the app

From the project root:

```powershell
cd deployment
.\stop.bat
```

### Notes

- The launcher scripts are located in deployment/start.ps1 and deployment/stop.ps1.
- Logs are stored in deployment/logs.
- If PowerShell blocks script execution, the .bat files bypass that restriction.
