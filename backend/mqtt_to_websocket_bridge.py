#!/usr/bin/env python3
"""
MQTT to WebSocket Bridge - Enhanced Communication Bridge

Bridges MQTT messages from the face tracking system to WebSocket clients
with additional processing and analytics for enhanced functionality.

Features:
- MQTT message subscription and processing
- Message enrichment and analytics
- Real-time data transformation
- Performance monitoring
- Error handling and recovery
- Data aggregation and statistics
"""

import asyncio
import json
import time
import logging
import threading
from typing import Dict, Any, Optional
from collections import defaultdict, deque
import paho.mqtt.client as mqtt
from websocket_server import get_api_instance

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MQTTToWebSocketBridge:
    """Enhanced MQTT to WebSocket bridge with analytics"""
    
    def __init__(self, broker_host="127.0.0.1", broker_port=1883, team_id="elvin01"):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.team_id = team_id
        
        # MQTT topics
        self.movement_topic = f"vision/{team_id}/movement"
        self.heartbeat_topic = f"vision/{team_id}/heartbeat"
        
        # MQTT client
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        # Analytics and tracking
        self.message_count = 0
        self.status_counts = defaultdict(int)
        self.confidence_history = deque(maxlen=100)
        self.message_timestamps = deque(maxlen=1000)
        self.last_message_time = 0
        
        # Performance metrics
        self.start_time = time.time()
        self.connection_drops = 0
        self.reconnect_attempts = 0
        
        # Enhanced features
        self.movement_patterns = defaultdict(list)
        self.face_lock_sessions = []
        self.current_session = None
        
        # WebSocket API reference
        self.websocket_api = None
        
    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            
            # Subscribe to topics
            client.subscribe(self.movement_topic)
            client.subscribe(self.heartbeat_topic)
            logger.info(f"Subscribed to topics: {self.movement_topic}, {self.heartbeat_topic}")
            
            # Reset reconnection counter
            self.reconnect_attempts = 0
            
        else:
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
            
    def _on_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        logger.warning(f"Disconnected from MQTT broker. Return code: {rc}")
        self.connection_drops += 1
        
    def _on_message(self, client, userdata, msg):
        """MQTT message callback with enhanced processing"""
        try:
            # Parse message
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            timestamp = time.time()
            
            # Update tracking
            self.message_count += 1
            self.message_timestamps.append(timestamp)
            self.last_message_time = timestamp
            
            # Process based on topic
            if topic == self.movement_topic:
                self._process_movement_message(payload, timestamp)
            elif topic == self.heartbeat_topic:
                self._process_heartbeat_message(payload, timestamp)
                
            # Send to WebSocket clients
            asyncio.create_task(self._send_to_websocket(payload, topic))
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse MQTT message: {e}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
            
    def _process_movement_message(self, payload: Dict[str, Any], timestamp: float):
        """Process movement detection messages with analytics"""
        status = payload.get("status", "UNKNOWN")
        confidence = payload.get("confidence", 0.0)
        
        # Update status counts
        self.status_counts[status] += 1
        
        # Track confidence history
        if confidence > 0:
            self.confidence_history.append(confidence)
            
        # Track movement patterns
        if status in ["MOVE_LEFT", "MOVE_RIGHT"]:
            self.movement_patterns[status].append(timestamp)
            
        # Track face lock sessions
        if status != "NO_FACE":
            if self.current_session is None:
                # Start new session
                self.current_session = {
                    "start_time": timestamp,
                    "status_changes": [(timestamp, status)],
                    "max_confidence": confidence
                }
            else:
                # Update current session
                self.current_session["status_changes"].append((timestamp, status))
                self.current_session["max_confidence"] = max(
                    self.current_session["max_confidence"], confidence
                )
        else:
            # End current session
            if self.current_session is not None:
                self.current_session["end_time"] = timestamp
                self.current_session["duration"] = timestamp - self.current_session["start_time"]
                self.face_lock_sessions.append(self.current_session)
                self.current_session = None
                
        # Enhanced message enrichment
        payload["processed_at"] = timestamp
        payload["message_sequence"] = self.message_count
        payload["avg_confidence_recent"] = self._get_recent_avg_confidence()
        payload["movement_rate"] = self._calculate_movement_rate()
        
    def _process_heartbeat_message(self, payload: Dict[str, Any], timestamp: float):
        """Process heartbeat messages with system metrics"""
        # Enrich heartbeat with bridge metrics
        payload["bridge_metrics"] = {
            "messages_processed": self.message_count,
            "connection_drops": self.connection_drops,
            "uptime": timestamp - self.start_time,
            "messages_per_second": self._calculate_message_rate()
        }
        
    def _get_recent_avg_confidence(self) -> float:
        """Calculate average confidence from recent messages"""
        if not self.confidence_history:
            return 0.0
        return sum(self.confidence_history) / len(self.confidence_history)
        
    def _calculate_movement_rate(self) -> float:
        """Calculate recent movement rate (movements per second)"""
        if not self.movement_patterns:
            return 0.0
            
        recent_time = time.time() - 10  # Last 10 seconds
        total_movements = 0
        
        for status, timestamps in self.movement_patterns.items():
            recent_movements = [t for t in timestamps if t > recent_time]
            total_movements += len(recent_movements)
            
        return total_movements / 10.0  # movements per second
        
    def _calculate_message_rate(self) -> float:
        """Calculate overall message rate"""
        if not self.message_timestamps:
            return 0.0
            
        # Calculate rate over last minute
        one_minute_ago = time.time() - 60
        recent_messages = [t for t in self.message_timestamps if t > one_minute_ago]
        return len(recent_messages) / 60.0
        
    async def _send_to_websocket(self, payload: Dict[str, Any], topic: str):
        """Send processed message to WebSocket clients"""
        try:
            # Get WebSocket API instance
            if self.websocket_api is None:
                self.websocket_api = get_api_instance()
                
            # Add topic information
            payload["mqtt_topic"] = topic
            payload["bridge_enhanced"] = True
            
            # Send to WebSocket clients
            await self.websocket_api.send_tracking_update(payload)
            
        except Exception as e:
            logger.error(f"Error sending to WebSocket: {e}")
            
    def get_analytics(self) -> Dict[str, Any]:
        """Get comprehensive analytics data"""
        current_time = time.time()
        
        return {
            "message_statistics": {
                "total_messages": self.message_count,
                "messages_per_second": self._calculate_message_rate(),
                "last_message_age": current_time - self.last_message_time if self.last_message_time else 0
            },
            "status_distribution": dict(self.status_counts),
            "confidence_statistics": {
                "average_confidence": self._get_recent_avg_confidence(),
                "confidence_samples": len(self.confidence_history)
            },
            "movement_patterns": {
                "left_movements": len(self.movement_patterns["MOVE_LEFT"]),
                "right_movements": len(self.movement_patterns["MOVE_RIGHT"]),
                "movement_rate": self._calculate_movement_rate()
            },
            "session_statistics": {
                "total_sessions": len(self.face_lock_sessions),
                "active_session": self.current_session is not None,
                "average_session_duration": self._calculate_avg_session_duration()
            },
            "bridge_metrics": {
                "uptime": current_time - self.start_time,
                "connection_drops": self.connection_drops,
                "reconnect_attempts": self.reconnect_attempts
            }
        }
        
    def _calculate_avg_session_duration(self) -> float:
        """Calculate average face lock session duration"""
        if not self.face_lock_sessions:
            return 0.0
            
        durations = [s.get("duration", 0) for s in self.face_lock_sessions]
        return sum(durations) / len(durations)
        
    def connect(self):
        """Connect to MQTT broker"""
        try:
            logger.info(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from MQTT broker"""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Disconnected from MQTT broker")
        except Exception as e:
            logger.error(f"Error disconnecting from MQTT broker: {e}")
            
    def run_forever(self):
        """Run the bridge forever with automatic reconnection"""
        while True:
            try:
                if not self.connect():
                    logger.error("Failed to connect, retrying in 5 seconds...")
                    time.sleep(5)
                    self.reconnect_attempts += 1
                    continue
                    
                # Keep the main thread alive
                while True:
                    time.sleep(1)
                    
                    # Check connection health
                    if not self.client.is_connected():
                        logger.warning("MQTT connection lost, attempting to reconnect...")
                        break
                        
            except KeyboardInterrupt:
                logger.info("Shutting down MQTT to WebSocket bridge...")
                break
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                time.sleep(5)
                
        self.disconnect()

# Global instance
bridge_instance = MQTTToWebSocketBridge()

def get_bridge_instance():
    """Get the global bridge instance"""
    return bridge_instance

if __name__ == "__main__":
    # Run the bridge
    bridge_instance.run_forever()
