import time
from CANBus import *

if __name__ == "__main__":
    # Initialize CAN bus
    can_bus = CanBus()

    # Create ECUs with different arbitration IDs (lower = higher priority)
    ecu1 = ECU("ECU1", can_bus, arbitration_id=0x100)
    ecu2 = ECU("ECU2", can_bus, arbitration_id=0x080)
    ecu3 = ECU("ECU3", can_bus, arbitration_id=0x200)
    ecu4 = ECU("ECU4", can_bus, arbitration_id=0x050)  # Highest priority

    # Simulate sending packets
    print("\n--- Sending Packets ---\n")

    # ECU1 sends a message
    ecu1.send([0x11, 0x22])

    # ECU2 tries to send while ECU1 is transmitting
    ecu2.send([0x33, 0x44])

    # ECU3 also tries to send during the same busy period
    ecu3.send([0x55, 0x66, 0x77])

    # ECU4 tries to send (has highest priority arbitration ID)
    ecu4.send([0xAA])

    # Give time for all queued packets to finish transmitting
    time.sleep(5)
