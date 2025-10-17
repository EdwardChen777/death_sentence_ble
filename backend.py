from flask import Flask, request, jsonify, send_from_directory
import asyncio
from bleak import BleakClient
import os

app = Flask(__name__)

# Device configuration - update with your actual device details
BLE_ADDRESS = "FC28F7A3-F547-7342-1F57-BB2939694BDC"
WRITE_CHAR_UUID = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"

def crc16_modbus(data: bytes) -> bytes:
    """Calculate CRC16 Modbus checksum"""
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    # Return in big-endian format to match the examples
    return bytes([(crc >> 8) & 0xFF, crc & 0xFF])

def build_scent_command(scent_id: int, duration_sec: int) -> bytes:
    """Build scent command with correct CRC encoding"""
    start = bytes([0xF5])
    header = bytes([0x00, 0x00, 0x00, 0x01])
    cmd_type = bytes([0x02])
    subcmd = bytes([0x05])
    channel = bytes([scent_id])
    padding = bytes([0x00, 0x00])
    
    # Convert duration to milliseconds (2 bytes, big-endian)
    duration_ms = duration_sec * 1000
    duration_bytes = duration_ms.to_bytes(2, 'big')
    
    # Body for CRC calculation (everything except start, crc, and end)
    body = header + cmd_type + subcmd + channel + padding + duration_bytes
    
    # Calculate CRC
    crc_bytes = crc16_modbus(body)
    
    # End byte
    end = bytes([0x55])
    
    # Complete command
    return start + body + crc_bytes + end

async def play_scent_ble(scent_id: int, duration: int):
    """Send a single scent command to the device"""
    try:
        async with BleakClient(BLE_ADDRESS) as client:
            print(f"Connecting to device {BLE_ADDRESS}...")
            await client.connect()
            
            if not client.is_connected:
                print("Failed to connect to device!")
                return {"status": "error", "message": "Failed to connect to device"}
            
            print("Connected successfully!")
            
            # Build command with correct CRC
            cmd_bytes = build_scent_command(scent_id, duration)
            print(f"Sending scent {scent_id} for {duration}s...")
            print(f"Command bytes: {cmd_bytes.hex().upper()}")
            
            # Write to the characteristic
            await client.write_gatt_char(WRITE_CHAR_UUID, cmd_bytes)
            print(f"Successfully sent scent {scent_id} for {duration}s")
            
            return {"status": "success", "message": f"Scent {scent_id} sent for {duration} seconds"}
            
    except Exception as e:
        print(f"Error sending scent: {e}")
        return {"status": "error", "message": str(e)}

async def play_sequence_ble(sequence):
    """Send a sequence of scents to the device"""
    try:
        async with BleakClient(BLE_ADDRESS) as client:
            print(f"Connecting to device {BLE_ADDRESS}...")
            await client.connect()
            
            if not client.is_connected:
                print("Failed to connect to device!")
                return {"status": "error", "message": "Failed to connect to device"}
            
            print("Connected successfully!")
            
            for item in sequence:
                scent_id = item.get('scent_id', item.get('id', 1))
                duration = item.get('duration', 5)
                
                try:
                    # Build command with correct CRC
                    cmd_bytes = build_scent_command(scent_id, duration)
                    print(f"Sending scent {scent_id} for {duration}s...")
                    print(f"Command bytes: {cmd_bytes.hex().upper()}")
                    
                    # Write to the characteristic
                    await client.write_gatt_char(WRITE_CHAR_UUID, cmd_bytes)
                    print(f"Successfully sent scent {scent_id} for {duration}s")
                    
                    # Wait while scent plays
                    await asyncio.sleep(duration)
                    
                except Exception as e:
                    print(f"Error sending scent {scent_id}: {e}")
                    continue
            
            return {"status": "success", "message": "Sequence completed"}
            
    except Exception as e:
        print(f"Connection error: {e}")
        return {"status": "error", "message": str(e)}

@app.route('/play_scent', methods=['POST'])
def play_scent():
    """API endpoint to play a single scent"""
    try:
        data = request.get_json()
        scent_id = data.get('scent_id', 1)
        duration = data.get('duration', 5)
        
        # Validate input
        if not isinstance(scent_id, int) or scent_id < 1 or scent_id > 12:
            return jsonify({"status": "error", "message": "Invalid scent_id. Must be between 1-12"}), 400
        
        if not isinstance(duration, int) or duration < 1 or duration > 60:
            return jsonify({"status": "error", "message": "Invalid duration. Must be between 1-60 seconds"}), 400
        
        # Run the async function
        result = asyncio.run(play_scent_ble(scent_id, duration))
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/play_sequence', methods=['POST'])
def play_sequence():
    """API endpoint to play a sequence of scents"""
    try:
        data = request.get_json()
        sequence = data.get('sequence', [])
        
        if not sequence:
            return jsonify({"status": "error", "message": "No sequence provided"}), 400
        
        # Validate sequence
        for i, item in enumerate(sequence):
            if not isinstance(item, dict):
                return jsonify({"status": "error", "message": f"Item {i} must be a dictionary"}), 400
            
            scent_id = item.get('scent_id', item.get('id', 1))
            duration = item.get('duration', 5)
            
            if not isinstance(scent_id, int) or scent_id < 1 or scent_id > 12:
                return jsonify({"status": "error", "message": f"Invalid scent_id in item {i}. Must be between 1-12"}), 400
            
            if not isinstance(duration, int) or duration < 1 or duration > 60:
                return jsonify({"status": "error", "message": f"Invalid duration in item {i}. Must be between 1-60 seconds"}), 400
        
        # Run the async function
        result = asyncio.run(play_sequence_ble(sequence))
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "ok", "message": "Backend is running"})

@app.route('/')
def index():
    """Serve the frontend HTML file"""
    return send_from_directory('.', 'frontend.html')

if __name__ == "__main__":
    print("Starting DeathScent Backend Server...")
    print(f"Device Address: {BLE_ADDRESS}")
    print(f"Characteristic UUID: {WRITE_CHAR_UUID}")
    print("Frontend will be available at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
