# Deployment Guide

## Quick Start Deployment

This guide provides step-by-step instructions for deploying the AI Face Tracking System in various environments.

## Prerequisites

### Hardware Requirements
- **PC/Laptop**: Windows 10/11, macOS 10.15+, or Ubuntu 18.04+
- **RAM**: Minimum 4GB, recommended 8GB+
- **Storage**: 2GB free space
- **Webcam**: USB webcam or integrated camera
- **ESP8266**: NodeMCU or similar development board
- **Servo Motor**: SG90 or compatible servo
- **Network**: Local WiFi network

### Software Requirements
- **Python**: 3.9 or higher
- **Git**: For cloning repository
- **Mosquitto**: MQTT broker
- **VS Code**: Recommended IDE (optional)

## Installation Steps

### 1. System Preparation

#### Windows
```powershell
# Install Python from python.org
# Verify installation
python --version
pip --version

# Install Git
# Download from git-scm.com

# Install Mosquitto
# Download from mosquitto.org
# Add to PATH during installation
```

#### macOS
```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python git mosquitto

# Start Mosquitto service
brew services start mosquitto
```

#### Linux (Ubuntu/Debian)
```bash
# Update package manager
sudo apt update

# Install dependencies
sudo apt install python3 python3-pip git mosquitto mosquitto-clients

# Start Mosquitto service
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

### 2. Project Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/AI-Face-Tracking-System-using-MQTT.git
cd AI-Face-Tracking-System-using-MQTT

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install additional dependencies for enhanced features
pip install websockets asyncio paho-mqtt
```

### 3. Model Download

```bash
# Download face recognition model
curl -L -o buffalo_l.zip "https://sourceforge.net/projects/insightface.mirror/files/v0.7/buffalo_l.zip/download"

# Extract model
unzip -o buffalo_l.zip

# Copy model to correct location
mkdir -p models
cp w600k_r50.onnx models/embedder_arcface.onnx

# Cleanup
rm -f buffalo_l.zip w600k_r50.onnx 1k3d68.onnx 2d106det.onnx det_10g.onnx genderage.onnx
```

### 4. Configuration

#### PC Vision Configuration
Edit `pc_vision/config.py`:
```python
# MQTT Broker Settings
MQTT_BROKER_IP = "127.0.0.1"  # Localhost for single PC setup
MQTT_BROKER_PORT = 1883

# Team Identification
TEAM_ID = "team01"  # Change to your team ID

# Camera Settings
CAMERA_INDEX = 0  # Change if you have multiple cameras

# Movement Detection
DEAD_ZONE_RATIO = 0.12  # 12% tolerance
MIN_PUBLISH_INTERVAL = 0.5  # Anti-flooding protection
```

#### ESP8266 Configuration
Edit `esp8266/config.py`:
```python
# WiFi Settings
WIFI_SSID = "YOUR_WIFI_NAME"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# MQTT Broker (your PC's IP address)
MQTT_BROKER = "192.168.1.100"  # Change to your PC's IP
MQTT_PORT = 1883

# Team ID
TEAM_ID = "team01"  # Must match PC configuration

# Servo Settings
SERVO_PIN = 14  # GPIO14 (D5 on NodeMCU)
SERVO_STEP = 5  # Degrees per movement
```

## Hardware Setup

### ESP8266 Wiring

```
ESP8266 NodeMCU    SG90 Servo Motor
    D5 (GPIO14) ────→ Signal (Orange wire)
    3V3           ────→ Power   (Red wire)
    GND           ────→ Ground  (Brown wire)
```

### Wiring Diagram
```
      ESP8266                SG90 Servo
    ┌─────────┐            ┌─────────────┐
    │         │            │             │
    │   D5    ├────────────► Signal      │
    │         │            │             │
    │   3V3   ├────────────► Power       │
    │         │            │             │
    │   GND   ├────────────► Ground      │
    │         │            │             │
    └─────────┘            └─────────────┘
```

## Deployment Scenarios

### Scenario 1: Single PC Setup (Development)

**Use Case**: Development and testing on single machine

**Network Configuration**:
- MQTT Broker: localhost (127.0.0.1)
- WebSocket Server: localhost (127.0.0.1:9002)
- ESP8266 connects to PC's local IP

**Steps**:
1. Start MQTT broker
2. Start WebSocket server
3. Run PC vision module
4. Upload ESP8266 firmware
5. Open dashboard

```bash
# Terminal 1: Start MQTT broker
mosquitto -c mosquitto.conf

# Terminal 2: Start WebSocket server
python backend/websocket_server.py

# Terminal 3: Start MQTT bridge
python backend/mqtt_to_websocket_bridge.py

# Terminal 4: Run PC vision
python -m pc_vision.main

# Terminal 5: Upload ESP8266 (one-time)
python upload_to_esp.py

# Browser: Open dashboard
open dashboard/enhanced_dashboard.html
```

### Scenario 2: Multi-PC Network Setup

**Use Case**: Multiple users in same network

**Network Configuration**:
- MQTT Broker: Dedicated server IP (e.g., 192.168.1.10)
- Each PC uses unique TEAM_ID
- ESP8266 connects to broker IP

**Steps**:
1. Set up dedicated MQTT broker
2. Configure each PC with unique TEAM_ID
3. Update ESP8266 to connect to broker IP
4. Deploy dashboard to web server

### Scenario 3: Production Deployment

**Use Case**: Exhibition or demonstration

**Network Configuration**:
- Dedicated MQTT broker with persistence
- Load-balanced WebSocket servers
- Multiple ESP8266 devices
- Remote dashboard hosting

**Additional Components**:
- Nginx for reverse proxy
- SSL certificates for HTTPS
- Monitoring and logging
- Backup power supply

## Operation Procedures

### Startup Sequence

1. **Network Check**
```bash
# Verify MQTT broker
mosquitto_pub -h 127.0.0.1 -t "test" -m "hello"

# Check camera
python -c "import cv2; print(cv2.VideoCapture(0).isOpened())"
```

2. **Service Startup**
```bash
# Start all services in order
./scripts/start_services.sh
```

3. **System Verification**
```bash
# Check all components
./scripts/verify_system.sh
```

### Face Enrollment

```bash
# Run enrollment tool
python -m src.enroll

# Follow prompts:
# 1. Enter person's name
# 2. Position face in camera
# 3. Press SPACE to capture (15-20 samples)
# 4. Press 's' to save enrollment
```

### Daily Operation

1. **Start System**
```bash
# Quick start script
./scripts/daily_start.sh
```

2. **Monitor Dashboard**
- Open `http://localhost:8000/dashboard/enhanced_dashboard.html`
- Verify connection status
- Check face tracking performance

3. **Shutdown**
```bash
# Graceful shutdown
./scripts/shutdown.sh
```

## Troubleshooting

### Common Issues

#### MQTT Connection Failed
```bash
# Check if Mosquitto is running
ps aux | grep mosquitto

# Test connection
mosquitto_pub -h 127.0.0.1 -t "test" -m "hello"

# Check logs
tail -f /var/log/mosquitto/mosquitto.log
```

#### Camera Not Found
```bash
# List available cameras
python -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).isOpened()])"

# Update CAMERA_INDEX in config.py
```

#### ESP8266 Not Connecting
1. Check WiFi credentials in `esp8266/config.py`
2. Verify MQTT_BROKER IP matches your PC
3. Check ESP8266 serial output:
```bash
# Monitor ESP8266 output
python -c "
import serial
ser = serial.Serial('COM3', 115200)  # Windows
# ser = serial.Serial('/dev/ttyUSB0', 115200)  # Linux
while True:
    print(ser.readline().decode().strip())
"
```

#### Performance Issues
1. Reduce camera resolution
2. Adjust recognition interval
3. Close unnecessary applications
4. Check CPU usage

### Debug Mode

Enable verbose logging:
```python
# In pc_vision/config.py
DEBUG_LEVEL = "DEBUG"

# Or set environment variable
export DEBUG=DEBUG
python -m pc_vision.main
```

## Maintenance

### Regular Tasks

**Weekly**:
- Check system logs for errors
- Verify face recognition accuracy
- Update face database if needed

**Monthly**:
- Update Python packages
- Check for security updates
- Backup configuration files

**Quarterly**:
- Full system testing
- Performance benchmarking
- Hardware inspection

### Backup Procedures

```bash
# Backup face database
cp -r data/db/ backups/db_$(date +%Y%m%d)/

# Backup configuration
cp pc_vision/config.py backups/config_$(date +%Y%m%d).py
cp esp8266/config.py backups/esp_config_$(date +%Y%m%d).py

# Export face history
python scripts/export_history.py
```

### Performance Monitoring

Monitor key metrics:
- CPU usage (should be < 30%)
- Memory usage (should be < 1GB)
- Network latency (should be < 10ms)
- Face recognition FPS (should be > 10)

## Security Considerations

### Network Security
- Use WPA2/WPA3 WiFi encryption
- Change default MQTT credentials
- Use firewall to restrict access
- Consider VPN for remote access

### Data Privacy
- Face data stored locally only
- Regular cleanup of old history files
- Secure backup storage
- Access control for configuration files

## Scaling and Optimization

### Performance Tuning

**CPU Optimization**:
```python
# In pc_vision/config.py
RECOGNITION_INTERVAL = 20  # Reduce from 15
MIN_FACE_SIZE = 80         # Increase from 60
```

**Network Optimization**:
```python
# Reduce MQTT message frequency
MIN_PUBLISH_INTERVAL = 1.0  # Increase from 0.5
```

### Multi-User Deployment

For multiple simultaneous users:
1. Use unique TEAM_ID for each user
2. Deploy load-balanced MQTT broker
3. Use Redis for session management
4. Implement user authentication

## Automation Scripts

### Service Management Scripts

**start_services.sh**:
```bash
#!/bin/bash
echo "Starting Face Tracking System services..."

# Start MQTT broker
sudo systemctl start mosquitto

# Start WebSocket server
python backend/websocket_server.py &
WS_PID=$!

# Start MQTT bridge
python backend/mqtt_to_websocket_bridge.py &
BRIDGE_PID=$!

echo "Services started. PIDs: WS=$WS_PID, BRIDGE=$BRIDGE_PID"
```

**shutdown.sh**:
```bash
#!/bin/bash
echo "Shutting down Face Tracking System..."

# Kill Python processes
pkill -f "websocket_server.py"
pkill -f "mqtt_to_websocket_bridge.py"
pkill -f "pc_vision.main"

# Stop MQTT broker
sudo systemctl stop mosquitto

echo "System shutdown complete."
```

### Health Check Script

**health_check.sh**:
```bash
#!/bin/bash
echo "Face Tracking System Health Check"

# Check MQTT broker
if pgrep mosquitto > /dev/null; then
    echo "✓ MQTT broker running"
else
    echo "✗ MQTT broker not running"
fi

# Check WebSocket server
if curl -s http://localhost:9002 > /dev/null; then
    echo "✓ WebSocket server responding"
else
    echo "✗ WebSocket server not responding"
fi

# Check camera
if python -c "import cv2; cv2.VideoCapture(0).isOpened()"; then
    echo "✓ Camera accessible"
else
    echo "✗ Camera not accessible"
fi

echo "Health check complete."
```

---

This deployment guide provides comprehensive instructions for setting up, operating, and maintaining the AI Face Tracking System in various environments. Follow these procedures carefully to ensure reliable operation and optimal performance.
