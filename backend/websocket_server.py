#!/usr/bin/env python3
"""
WebSocket API Service - Enhanced Real-time Communication

Translates MQTT updates into real-time dashboard updates with additional
features for originality and enhanced user experience.

Features:
- Real-time face tracking visualization
- Historical data streaming
- System performance metrics
- Multi-client support
- Connection management
- Data aggregation and analytics
"""

import asyncio
import websockets
import json
import time
import logging
from typing import Dict, List, Set
from dataclasses import dataclass, asdict
import threading
from collections import deque

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TrackingEvent:
    """Face tracking event data structure"""
    timestamp: float
    status: str
    confidence: float
    servo_angle: int = 90
    face_position: tuple = (0, 0)
    lock_state: str = "SEARCHING"
    fps: float = 0.0
    actions_detected: List[str] = None
    
    def __post_init__(self):
        if self.actions_detected is None:
            self.actions_detected = []

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    network_latency: float = 0.0
    mqtt_messages_sent: int = 0
    faces_detected: int = 0
    uptime: float = 0.0

class WebSocketAPI:
    """Enhanced WebSocket API for face tracking dashboard"""
    
    def __init__(self, host="127.0.0.1", port=9002):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.current_event = TrackingEvent(
            timestamp=time.time(),
            status="NO_FACE",
            confidence=0.0
        )
        self.metrics = SystemMetrics()
        self.event_history = deque(maxlen=100)  # Keep last 100 events
        self.start_time = time.time()
        self._lock = threading.Lock()
        
        # Enhanced features
        self.action_counts = {}
        self.status_duration = {}
        self.last_status_change = time.time()
        self.total_faces_detected = 0
        
    async def register_client(self, websocket):
        """Register a new client connection"""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
        
        # Send current state immediately
        await self.send_to_client(websocket, {
            "type": "initial_state",
            "event": asdict(self.current_event),
            "metrics": asdict(self.metrics),
            "history": [asdict(e) for e in list(self.event_history)[-10:]]
        })
        
    async def unregister_client(self, websocket):
        """Unregister a client connection"""
        self.clients.discard(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
        
    async def send_to_client(self, websocket, data):
        """Send data to a specific client"""
        try:
            await websocket.send(json.dumps(data))
        except websockets.exceptions.ConnectionClosed:
            await self.unregister_client(websocket)
            
    async def broadcast(self, data):
        """Broadcast data to all connected clients"""
        if not self.clients:
            return
            
        disconnected = set()
        for client in self.clients:
            try:
                await client.send(json.dumps(data))
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
                
        # Remove disconnected clients
        for client in disconnected:
            await self.unregister_client(client)
            
    def update_tracking_event(self, event_data: dict):
        """Update current tracking event from MQTT data"""
        with self._lock:
            # Update current event
            self.current_event.timestamp = time.time()
            self.current_event.status = event_data.get("status", "NO_FACE")
            self.current_event.confidence = event_data.get("confidence", 0.0)
            
            # Track status changes for analytics
            if self.current_event.status != getattr(self, '_last_status', 'NO_FACE'):
                self._last_status = self.current_event.status
                self.last_status_change = time.time()
                
                # Update status duration tracking
                status_key = self.current_event.status
                if status_key not in self.status_duration:
                    self.status_duration[status_key] = 0
                self.status_duration[status_key] += 1
                
            # Add to history
            self.event_history.append(TrackingEvent(**asdict(self.current_event)))
            
            # Update metrics
            if self.current_event.status != "NO_FACE":
                self.total_faces_detected += 1
                self.metrics.faces_detected = self.total_faces_detected
                
    def update_metrics(self, **kwargs):
        """Update system metrics"""
        with self._lock:
            for key, value in kwargs.items():
                if hasattr(self.metrics, key):
                    setattr(self.metrics, key, value)
            
            # Update uptime
            self.metrics.uptime = time.time() - self.start_time
            
    async def send_tracking_update(self, event_data: dict):
        """Send tracking update to all clients"""
        self.update_tracking_event(event_data)
        
        # Prepare enhanced message
        message = {
            "type": "tracking_update",
            "event": asdict(self.current_event),
            "metrics": asdict(self.metrics),
            "analytics": {
                "status_distribution": dict(self.status_duration),
                "total_events": len(self.event_history),
                "average_confidence": self._calculate_avg_confidence()
            }
        }
        
        await self.broadcast(message)
        
    async def send_metrics_update(self):
        """Send periodic metrics update"""
        self.update_metrics()
        
        message = {
            "type": "metrics_update",
            "metrics": asdict(self.metrics),
            "performance": {
                "events_per_second": len(self.event_history) / max(1, self.metrics.uptime),
                "client_count": len(self.clients),
                "memory_efficiency": self._calculate_memory_efficiency()
            }
        }
        
        await self.broadcast(message)
        
    def _calculate_avg_confidence(self) -> float:
        """Calculate average confidence from recent events"""
        if not self.event_history:
            return 0.0
        recent_events = list(self.event_history)[-20:]  # Last 20 events
        confidences = [e.confidence for e in recent_events if e.confidence > 0]
        return sum(confidences) / len(confidences) if confidences else 0.0
        
    def _calculate_memory_efficiency(self) -> float:
        """Calculate memory efficiency metric"""
        # Simple heuristic based on history size and max size
        return len(self.event_history) / 100.0  # Percentage of buffer used
        
    async def handle_client_message(self, websocket, message):
        """Handle incoming messages from clients"""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "request_history":
                # Send historical data
                history_data = {
                    "type": "history_response",
                    "history": [asdict(e) for e in list(self.event_history)],
                    "analytics": {
                        "status_distribution": dict(self.status_duration),
                        "total_events": len(self.event_history)
                    }
                }
                await self.send_to_client(websocket, history_data)
                
            elif msg_type == "request_metrics":
                # Send detailed metrics
                metrics_data = {
                    "type": "metrics_response",
                    "metrics": asdict(self.metrics),
                    "analytics": {
                        "average_confidence": self._calculate_avg_confidence(),
                        "memory_efficiency": self._calculate_memory_efficiency(),
                        "events_per_second": len(self.event_history) / max(1, self.metrics.uptime)
                    }
                }
                await self.send_to_client(websocket, metrics_data)
                
            elif msg_type == "ping":
                # Respond to ping for latency measurement
                await self.send_to_client(websocket, {"type": "pong", "timestamp": time.time()})
                
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON received from client: {message}")
            
    async def client_handler(self, websocket, path):
        """Handle individual client connection"""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_client_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
            
    async def metrics_loop(self):
        """Periodic metrics update loop"""
        while True:
            try:
                await self.send_metrics_update()
                await asyncio.sleep(5)  # Update every 5 seconds
            except Exception as e:
                logger.error(f"Error in metrics loop: {e}")
                await asyncio.sleep(1)
                
    async def start_server(self):
        """Start the WebSocket server"""
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        
        # Start metrics update loop
        asyncio.create_task(self.metrics_loop())
        
        # Start WebSocket server
        async with websockets.serve(self.client_handler, self.host, self.port):
            logger.info(f"WebSocket server running on ws://{self.host}:{self.port}")
            await asyncio.Future()  # Run forever

# Global instance for external access
api_instance = WebSocketAPI()

def get_api_instance():
    """Get the global API instance"""
    return api_instance

async def send_tracking_update(event_data: dict):
    """Convenience function to send tracking updates"""
    await api_instance.send_tracking_update(event_data)

if __name__ == "__main__":
    # Run the server
    asyncio.run(api_instance.start_server())
