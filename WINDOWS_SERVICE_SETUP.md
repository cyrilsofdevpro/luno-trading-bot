# Windows Service Setup for Luno Trading Bot

This guide helps you install the Luno Trading Bot dashboard as a Windows Service, ensuring it runs automatically on system startup and the auto-sell monitor remains active at all times.

## Table of Contents
- [Option 1: Using NSSM (Non-Sucking Service Manager) - Recommended](#option-1-using-nssm-recommended)
- [Option 2: Using PowerShell & sc (Built-in)](#option-2-using-powershell--sc)
- [Option 3: Using Task Scheduler](#option-3-using-task-scheduler)
- [Monitoring & Maintenance](#monitoring--maintenance)

---

## Option 1: Using NSSM (Recommended)

NSSM is a lightweight service manager that runs any executable as a Windows Service with automatic restart on crashes.

### Step 1: Download & Install NSSM

1. Go to https://nssm.cc/download
2. Download the latest version (typically `nssm-2.24-101-g897c7ad` or later)
3. Extract the ZIP to a folder, e.g., `C:\tools\nssm`
4. Add to PATH (optional, but recommended):
   - Open "Environment Variables" (search in Start menu)
   - Add `C:\tools\nssm` (or your extraction folder) to the System PATH
   - Restart PowerShell/Command Prompt

### Step 2: Install the Service

Open PowerShell as Administrator and run:

```powershell
# Navigate to your Luno bot directory
cd "C:\Users\Cyril Sofdev\Documents\Luno trading  Bot"

# Install the service using NSSM
nssm install LunoTradingBot "C:\path\to\python.exe" "dashboard.py"
```

Replace `C:\path\to\python.exe` with your Python executable path. To find it:

```powershell
python -c "import sys; print(sys.executable)"
```

### Step 3: Configure Service (Optional but Recommended)

```powershell
# Set the working directory for the service
nssm set LunoTradingBot AppDirectory "C:\Users\Cyril Sofdev\Documents\Luno trading  Bot"

# Auto-restart on crash after 5 seconds
nssm set LunoTradingBot AppRestartDelay 5000

# Redirect stdout/stderr to log files for debugging
nssm set LunoTradingBot AppStdout "C:\Users\Cyril Sofdev\Documents\Luno trading  Bot\service_output.log"
nssm set LunoTradingBot AppStderr "C:\Users\Cyril Sofdev\Documents\Luno trading  Bot\service_error.log"

# Set dependencies (if needed)
nssm set LunoTradingBot DependOnService Tcpip

# Set startup type to "Automatic" (start on boot)
nssm set LunoTradingBot Start SERVICE_AUTO_START
```

### Step 4: Start the Service

```powershell
# Start the service
nssm start LunoTradingBot

# Verify it's running
Get-Service -Name LunoTradingBot

# Or from Services app: press Win+R, type "services.msc"
```

### Step 5: Check Status & Logs

```powershell
# Check service status
Get-Service -Name LunoTradingBot

# View service output log
Get-Content "C:\Users\Cyril Sofdev\Documents\Luno trading  Bot\service_output.log" -Tail 20

# View service error log
Get-Content "C:\Users\Cyril Sofdev\Documents\Luno trading  Bot\service_error.log" -Tail 20
```

### Useful NSSM Commands

```powershell
# Stop the service
nssm stop LunoTradingBot

# Restart the service
nssm restart LunoTradingBot

# Remove the service
nssm remove LunoTradingBot confirm

# Edit service settings in GUI
nssm edit LunoTradingBot
```

---

## Option 2: Using PowerShell & sc (Built-in)

This method uses Windows' built-in `sc.exe` command. It's less flexible than NSSM but requires no additional downloads.

### Step 1: Create a Batch Wrapper

Create a file named `run_dashboard.bat` in your bot directory:

```batch
@echo off
cd /d "C:\Users\Cyril Sofdev\Documents\Luno trading  Bot"
python dashboard.py
```

Make sure the batch file is executable and can find Python in your PATH.

### Step 2: Install the Service

Open PowerShell as Administrator:

```powershell
$pythonPath = (python -c "import sys; print(sys.executable)") -replace "\\", "\\"
$botDir = "C:\Users\Cyril Sofdev\Documents\Luno trading  Bot"
$exePath = "$botDir\run_dashboard.bat"

# Create the service (note: requires admin privileges)
sc.exe create LunoTradingBot binPath= $exePath

# Or for direct Python execution (more robust):
sc.exe create LunoTradingBot binPath= "`"$pythonPath`" `"$botDir\dashboard.py`"" start= auto
```

### Step 3: Start the Service

```powershell
# Start the service
Start-Service -Name LunoTradingBot

# Check status
Get-Service -Name LunoTradingBot
```

### Step 4: Remove the Service (if needed)

```powershell
# Stop the service
Stop-Service -Name LunoTradingBot

# Remove it
sc.exe delete LunoTradingBot
```

---

## Option 3: Using Task Scheduler

This is the simplest method but offers less robust auto-restart behavior.

### Step 1: Open Task Scheduler

Press `Win+R` → type `taskschd.msc` → press Enter

### Step 2: Create a Basic Task

1. Right-click "Task Scheduler Library" → "Create Basic Task"
2. Name: `Luno Trading Bot`
3. Description: `Runs Luno trading bot dashboard on startup`
4. Trigger: "At startup"
5. Action: "Start a program"
   - Program: `C:\path\to\python.exe`
   - Arguments: `dashboard.py`
   - Start in: `C:\Users\Cyril Sofdev\Documents\Luno trading  Bot`
6. Finish

### Step 3: Configure Advanced Options

1. Right-click the task → "Properties"
2. Go to "General" tab:
   - Check "Run with highest privileges"
3. Go to "Conditions" tab:
   - Uncheck "Start the task only if the computer is on AC power" (if using laptop)
4. Go to "Settings" tab:
   - Check "Run task as soon as possible after a scheduled start is missed"
   - Check "If the task fails, restart every:" and set to 1 minute
   - Set "Stop the task if it runs longer than:" to something reasonable (e.g., 23 hours)
5. Click OK

---

## Monitoring & Maintenance

### Check if Service is Running

```powershell
# Using Get-Service (PowerShell)
Get-Service -Name LunoTradingBot | Select-Object Status, DisplayName

# Or open Services app: Win+R → services.msc
```

### View Dashboard Logs

The dashboard logs are stored in:
- Main log: `bot.log`
- Auto-sell debug log: `autosell_debug.log` (if auto-sell is active)
- Service output: `service_output.log` (if using NSSM)

Check logs via PowerShell:

```powershell
cd "C:\Users\Cyril Sofdev\Documents\Luno trading  Bot"

# Last 50 lines of main log
Get-Content bot.log -Tail 50

# Last 50 lines of auto-sell debug log
Get-Content autosell_debug.log -Tail 50

# Stream logs in real-time
Get-Content bot.log -Tail 20 -Wait
```

### Verify Auto-Sell Monitor is Running

```powershell
# Query the dashboard API
Invoke-RestMethod -Uri 'http://127.0.0.1:5000/api/autosell/status' -UseBasicParsing | ConvertTo-Json
```

Expected output:
```json
{
  "success": true,
  "status": {
    "running": true,
    "pid": 12345,
    "target_pct": 2.0,
    "pair": "USDTNGN",
    ...
  }
}
```

### Restart the Service

```powershell
# Using Get-Service
Get-Service -Name LunoTradingBot | Restart-Service

# Or using NSSM
nssm restart LunoTradingBot

# Or stop and start manually
Stop-Service -Name LunoTradingBot
Start-Service -Name LunoTradingBot
```

### Uninstall the Service

```powershell
# Stop the service first
Stop-Service -Name LunoTradingBot

# Using NSSM
nssm remove LunoTradingBot confirm

# Using sc
sc.exe delete LunoTradingBot
```

---

## Troubleshooting

### Service Won't Start

1. **Check logs:**
   ```powershell
   Get-Content service_error.log -Tail 50
   ```

2. **Verify Python path:**
   ```powershell
   python -c "import sys; print(sys.executable)"
   ```

3. **Check working directory:**
   ```powershell
   cd "C:\Users\Cyril Sofdev\Documents\Luno trading  Bot"
   python dashboard.py  # Run manually to test
   ```

4. **Check for port conflicts:**
   ```powershell
   netstat -ano | findstr :5000
   ```

5. **Re-install the service:**
   ```powershell
   # NSSM
   nssm remove LunoTradingBot confirm
   nssm install LunoTradingBot "C:\path\to\python.exe" "dashboard.py"
   nssm set LunoTradingBot AppDirectory "C:\Users\Cyril Sofdev\Documents\Luno trading  Bot"
   nssm start LunoTradingBot
   ```

### Dashboard Port Already in Use

If you get an error about port 5000 being in use:

```powershell
# Find what's using port 5000
netstat -ano | findstr :5000

# Kill the process (replace PID with the actual PID)
taskkill /PID <PID> /F

# Or change the port in dashboard.py (if needed)
```

### Auto-Sell Monitor Not Running

If the auto-sell monitor is not active (status shows `"running": false`):

1. **Check auto_sell_monitor.py is in the directory:**
   ```powershell
   ls auto_sell_monitor.py
   ```

2. **Check debug log:**
   ```powershell
   Get-Content autosell_debug.log -Tail 50
   ```

3. **Manually start the monitor:**
   ```powershell
   python auto_sell_monitor.py
   ```

4. **Check watchdog logs:**
   The watchdog checks every 10 seconds and logs to `autosell_debug.log`. If it detects the monitor crashed, it should restart automatically.

---

## Security Considerations

1. **API Credentials:**
   - Store Luno API keys in `.env` or in per-user DB records
   - Never commit `.env` to version control
   - Restrict file permissions on `.env`:
     ```powershell
     icacls ".env" /inheritance:r /grant:r "%USERNAME%:F"
     ```

2. **Service Account:**
   - For production, consider running the service under a dedicated low-privilege account instead of SYSTEM
   - In NSSM: `nssm set LunoTradingBot ObjectName ".\ServiceUser" "Password"`

3. **Dashboard Access:**
   - Consider adding authentication/firewall rules to restrict dashboard access to localhost
   - Use a reverse proxy (nginx/Caddy) for production deployments

4. **Firewall:**
   - Ensure port 5000 (or configured port) is only accessible from trusted networks

---

## Next Steps

- Open the dashboard in your browser: `http://localhost:5000`
- Log in with your credentials
- Verify account balance and auto-sell monitor status
- Set up alerts/notifications if desired
- Monitor logs regularly for errors or unusual activity

For additional help, check the dashboard logs and the `autosell_debug.log` file.
