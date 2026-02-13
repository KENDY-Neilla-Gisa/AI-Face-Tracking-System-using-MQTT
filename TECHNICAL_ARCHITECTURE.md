# Technical Architecture Documentation

## System Overview

The AI Face Tracking System using MQTT is a sophisticated real-time computer vision application that demonstrates advanced integration between multiple technologies. This document provides detailed technical insights into the system's architecture, design decisions, and implementation details.

## Architecture Principles

### 1. Modular Design
The system follows a modular architecture where each component has a single responsibility:
- **PC Vision Module**: Face detection, recognition, and tracking
- **MQTT Broker**: Message routing and communication
- **ESP8266 Controller**: Hardware control and servo management
- **Web Dashboard**: Real-time visualization and monitoring

### 2. Asynchronous Communication
All communication between components is asynchronous and event-driven:
- MQTT for PC-to-ESP8266 communication
- WebSocket for dashboard real-time updates
- Non-blocking message processing

### 3. Fault Tolerance
The system includes multiple layers of error handling:
- Automatic reconnection for MQTT and WebSocket connections
- Graceful degradation when components are unavailable
- State recovery after connection loss

## Detailed Component Architecture

### PC Vision Module

#### Core Processing Pipeline
```
Camera Frame → Face Detection → Landmark Extraction → Face Alignment → 
Embedding Generation → Recognition → Movement Analysis → MQTT Publishing
```

#### Technical Implementation Details

**Face Detection (Haar Cascade)**
- Uses OpenCV's Haar cascade classifier for initial face detection
- Configurable minimum face size (default: 60px)
- Multi-scale detection with scaleFactor=1.1 and minNeighbors=5

**Landmark Extraction (MediaPipe)**
- 5-point facial landmark detection
- Points: left eye, right eye, nose tip, left mouth corner, right mouth corner
- Sub-pixel accuracy for precise alignment

**Face Alignment**
- Similarity transformation (rotation + scale + translation)
- Standardized output: 112×112 pixels
- Canonical pose normalization

**Recognition (ArcFace ONNX)**
- ResNet-50 backbone with 512-dimensional embeddings
- L2 normalization for cosine similarity computation
- Configurable distance threshold (default: 0.54)

**Movement Analysis**
- Dead-zone algorithm with configurable tolerance (12% default)
- State-based movement classification
- Anti-flooding protection (0.5s minimum publish interval)

#### Memory Management
- Efficient NumPy array operations
- Memory pooling for frequent allocations
- Garbage collection optimization

### MQTT Communication Layer

#### Message Protocol
**Movement Command Structure**
```json
{
  "status": "MOVE_LEFT|MOVE_RIGHT|CENTERED|NO_FACE",
  "confidence": 0.87,
  "timestamp": 1730000000,
  "face_position": {"x": 320, "y": 240},
  "bounding_box": {"x1": 200, "y1": 150, "x2": 400, "y2": 330}
}
```

**Topic Hierarchy**
- `vision/{team_id}/movement` - Movement commands
- `vision/{team_id}/heartbeat` - System status updates
- Team-based isolation for multi-deployment scenarios

#### Quality of Service
- QoS 0 (At most once) for real-time performance
- Automatic message deduplication
- Connection state monitoring

### ESP8266 Microcontroller

#### Hardware Abstraction
**Servo Control Interface**
```python
class Servo:
    def __init__(self, pin, freq=50, duty_min=40, duty_max=115)
    def set_angle(self, angle)  # 0-180 degrees
    def step_left(self, step=5)  # Incremental movement
    def step_right(self, step=5)
    def center(self)  # Return to neutral position
```

**PWM Configuration**
- 50Hz frequency (standard for servos)
- Duty cycle range: 40-115 (0.5ms to 2.5ms pulse)
- Linear interpolation for angle-to-duty conversion

#### Network Stack
**WiFi Connection Management**
- Automatic reconnection with exponential backoff
- Connection state monitoring
- Network health checks

**MQTT Client Implementation**
- Persistent session support
- Last Will and Testament (LWT) for offline detection
- Message buffering during disconnection

### Enhanced WebSocket API

#### Real-time Data Streaming
**Message Types**
- `tracking_update` - Real-time face tracking data
- `metrics_update` - System performance metrics
- `initial_state` - Connection initialization
- `history_response` - Historical data requests
- `analytics_update` - Statistical analysis

**Data Structures**
```python
@dataclass
class TrackingEvent:
    timestamp: float
    status: str
    confidence: float
    servo_angle: int
    face_position: tuple
    lock_state: str
    fps: float
    actions_detected: List[str]
```

#### Performance Optimizations
- Connection pooling for multiple clients
- Message batching for high-frequency updates
- Memory-efficient circular buffers
- Asynchronous I/O operations

## Data Flow Analysis

### Real-time Processing Path
1. **Camera Capture** (30 FPS)
2. **Face Detection** (10-15 FPS after optimization)
3. **Recognition** (5-10 FPS for multiple faces)
4. **Movement Analysis** (30 FPS)
5. **MQTT Publishing** (Throttled to 2 Hz max)
6. **ESP8266 Processing** (Immediate)
7. **Servo Movement** (100-200ms response time)

### Latency Breakdown
| Component | Typical Latency | Optimization |
|-----------|----------------|-------------|
| Camera Capture | 33ms | Hardware acceleration |
| Face Detection | 50ms | Multi-threading |
| Recognition | 30ms | ONNX Runtime optimization |
| Network Transfer | 5ms | Local network |
| ESP8266 Processing | 10ms | MicroPython optimization |
| Servo Response | 100ms | Hardware limitation |

## Performance Characteristics

### Throughput Metrics
- **Camera FPS**: 30 FPS (hardware dependent)
- **Detection FPS**: 15-20 FPS (single face)
- **Recognition FPS**: 10-15 FPS (cached embeddings)
- **MQTT Message Rate**: 2-5 Hz (anti-flooding)
- **WebSocket Updates**: 30-60 Hz (real-time dashboard)

### Resource Utilization
**PC Requirements**
- CPU: 10-20% (Intel i5 or equivalent)
- RAM: 500MB (including model loading)
- Network: <1 Mbps (local MQTT)
- Storage: 100MB (models and database)

**ESP8266 Requirements**
- Flash: 1MB (firmware + configuration)
- RAM: 80KB (runtime + buffers)
- Network: WiFi 2.4GHz
- GPIO: 1 pin (servo control)

## Security Considerations

### Network Security
- Local network deployment only
- No external internet connectivity required
- Team-based topic isolation
- Optional MQTT authentication

### Data Privacy
- All processing happens locally
- No cloud data transmission
- Face embeddings stored locally
- Configurable data retention policies

## Scalability Analysis

### Horizontal Scaling
- Multiple PC vision nodes possible
- Load balancing via MQTT topics
- Dashboard supports multiple concurrent clients
- ESP8266 can be replicated for multiple servos

### Vertical Scaling
- GPU acceleration for face recognition
- Higher resolution camera support
- Multiple face tracking capability
- Advanced servo control (multiple axes)

## Monitoring and Diagnostics

### System Health Metrics
- Connection status (MQTT, WebSocket)
- Processing latency
- Error rates and types
- Resource utilization

### Debugging Features
- Verbose logging with configurable levels
- Performance profiling hooks
- State inspection endpoints
- Real-time data export

## Integration Points

### External System Integration
**API Endpoints**
```python
# WebSocket API
ws://localhost:9002

# MQTT Topics
vision/team01/movement
vision/team01/heartbeat

# HTTP Endpoints (future)
GET /api/status
GET /api/metrics
POST /api/config
```

**Data Export Formats**
- JSON (real-time streaming)
- CSV (historical analysis)
- NPZ (face embeddings)
- MP4 (video recording)

## Development Guidelines

### Code Organization
```
src/
├── core/           # Core face recognition
├── detection/      # Face detection algorithms
├── tracking/       # Movement and tracking logic
├── communication/  # MQTT and WebSocket handlers
├── hardware/       # Hardware abstraction layer
└── utils/          # Utility functions
```

### Testing Strategy
- Unit tests for individual components
- Integration tests for data flow
- Performance benchmarks
- Hardware-in-the-loop testing

### Deployment Configuration
**Environment Variables**
```bash
MQTT_BROKER_HOST=127.0.0.1
MQTT_BROKER_PORT=1883
TEAM_ID=elvin01
CAMERA_INDEX=0
DEBUG_LEVEL=INFO
```

**Configuration Files**
- `pc_vision/config.py` - PC vision settings
- `esp8266/config.py` - Microcontroller settings
- `mosquitto.conf` - MQTT broker configuration

## Future Enhancements

### Technical Roadmap
1. **Multi-Face Tracking**: Simultaneous tracking of multiple faces
2. **3D Positioning**: Depth estimation with stereo cameras
3. **Machine Learning**: Adaptive threshold tuning
4. **Cloud Integration**: Optional cloud analytics
5. **Mobile Support**: Native mobile applications

### Research Opportunities
- Neural network acceleration
- Edge computing optimization
- Advanced servo control algorithms
- Real-time performance optimization

---

This technical architecture documentation provides a comprehensive understanding of the system's design, implementation details, and operational characteristics. It serves as a reference for developers, system administrators, and researchers working with or extending the face tracking system.
