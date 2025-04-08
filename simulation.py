import time
from CANBus import *
import threading

if __name__ == "__main__":
    # Initialize CAN bus
    can_bus = CanBus()

    # Create ECUs with different arbitration IDs (lower = higher priority)
    ecu1 = ECU("ECU1", can_bus, arbitration_id=0x100)
    ecu2 = ECU("ECU2", can_bus, arbitration_id=0x080)
    ecu3 = ECU("ECU3", can_bus, arbitration_id=0x200)
    ecu4 = ECU("ECU4", can_bus, arbitration_id=0x050)  # Highest priority

    # Simulate sending packets in parallel
    print("\n--- Sending Packets in Parallel ---\n")

    # Define threads for each ECU's send
    t1 = threading.Thread(target=ecu1.send, args=([0x11, 0x22],))
    time.sleep(1)
    t2 = threading.Thread(target=ecu2.send, args=([0x33, 0x44],))
    time.sleep(0.1)
    t3 = threading.Thread(target=ecu3.send, args=([0x55, 0x66, 0x77],))
    time.sleep(0.3)
    t4 = threading.Thread(target=ecu4.send, args=([0xAA],))

    # Start all threads
    t1.start()
    t2.start()
    t3.start()
    t4.start()

    # Wait for all to complete
    t1.join()
    t2.join()
    t3.join()
    t4.join()

    # Give time for the bus to finish transmitting any remaining packets
    time.sleep(5)
