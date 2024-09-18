import serial
import time

# Open serial port (change COM6 and baud rate if necessary)
ser = serial.Serial('COM6', 115200, timeout=0.001)

# Send the trigger sequence similar to the MATLAB version
ser.write(b'mh')  # Send 'mh' as two bytes
ser.write(bytes([20, 0]))  # Send 20 and 0 as bytes
ser.flush()

# Small delay (matching MATLAB's pause(0.02))
time.sleep(0.02)

# Reset trigger by sending 'mh' followed by 0, 0
ser.write(b'mh')
ser.write(bytes([0, 0]))  # Reset to 0
ser.flush()

# Close the port
ser.close()

print("Trigger sent")
