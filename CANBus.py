import random
import time

class CanPacket:
    """ Represents a CAN packet with an ID, data, and timestamp. """
    def __init__(self, arbitration_id, data):
        self.arbitration_id = arbitration_id  # Message ID
        self.data = data                      # Data payload (bytes)
        self.timestamp = time.time()          # Timestamp when created

    def __repr__(self):
        return f"CAN Packet(ID={hex(self.arbitration_id)}, Data={self.data}, Time={self.timestamp:.3f})"


class CanBus:
    """ Simulates a CAN bus where ECUs send and receive messages with error handling. """
    def __init__(self):
        self.listeners = []  # List of ECUs listening to the bus

    def register_ecu(self, ecu):
        """ Registers an ECU to listen on the CAN bus. """
        self.listeners.append(ecu)

    def send(self, packet, sender_ecu):
        """ Simulates sending a CAN packet with error handling. """
        if sender_ecu.is_bus_off():
            print(f"{sender_ecu.name} is in BUS-OFF! Cannot send: {packet}")
            return

        print(f"CAN Bus Transmitting: {packet}")

        # Notify all ECUs that a message was sent
        for ecu in self.listeners:
            if ecu != sender_ecu:
                ecu.receive(packet)

        # Simulate the arbitration phase (priority is based on the arbitration ID)
        self.arbitrate(packet, sender_ecu)

    def arbitrate(self, packet, sender_ecu):
        """ Simulates CAN arbitration (based on arbitration ID) """
        print(f"Arbitration in progress for {sender_ecu.name} with ID {hex(packet.arbitration_id)}")

        # First, sort all ECUs by arbitration ID (lowest priority ID wins arbitration)
        competing_ecus = [ecu for ecu in self.listeners if ecu != sender_ecu and not ecu.is_bus_off()]
        competing_ecus.append(sender_ecu)

        # Sort ECUs by their arbitration ID (ascending order, lowest wins)
        competing_ecus.sort(key=lambda ecu: ecu.arbitration_id)

        # The ECU with the lowest ID wins the arbitration
        winner_ecu = competing_ecus[0]
        print(f"Arbitration Winner: {winner_ecu.name} with ID {hex(winner_ecu.arbitration_id)}")
        
        # Notify all ECUs about the message
        for ecu in self.listeners:
            if ecu != winner_ecu:
                ecu.receive(packet)

        winner_ecu.TEC = max(0, winner_ecu.TEC - 1)  # Decrease TEC for the winner
        winner_ecu.update_error_state()
        print(f"{winner_ecu.name} Sent: {packet} | TEC: {winner_ecu.TEC} | State: {winner_ecu.error_state}")


class ECU:
    """ Represents an ECU with error handling and error flag management. """
    def __init__(self, name, can_bus, arbitration_id):
        self.name = name
        self.can_bus = can_bus
        self.arbitration_id = arbitration_id  # Unique ID for sending messages
        self.can_bus.register_ecu(self)  # Register ECU on the bus
        self.TEC = 0  # Transmit Error Counter
        self.REC = 0  # Receive Error Counter
        self.error_state = "ERROR-ACTIVE"  # ERROR-ACTIVE, ERROR-PASSIVE, BUS-OFF

    def update_error_state(self):
        """ Updates the ECU's error state based on TEC and REC. """
        if self.TEC >= 256:
            self.error_state = "BUS-OFF"
            print(f"{self.name} ENTERED BUS-OFF MODE!")
        elif self.TEC >= 128 or self.REC >= 128:
            self.error_state = "ERROR-PASSIVE"
        else:
            self.error_state = "ERROR-ACTIVE"

    def is_bus_off(self):
        """ Checks if the ECU is in BUS-OFF state. """
        return self.error_state == "BUS-OFF"

    def send(self, data):
        """ Creates and sends a CAN message, handling errors. """
        if self.is_bus_off():
            print(f"{self.name} is in BUS-OFF! Cannot send.")
            return

        packet = CanPacket(self.arbitration_id, data)

        # Simulate a bit error with 10% probability
        if random.random() < 0.1:  
            print(f"{self.name} BIT ERROR detected! Sending ERROR FLAG...")
            self.send_error_flag()
            return

        self.can_bus.send(packet, self)
        self.TEC = max(0, self.TEC - 1)  # Decrease TEC on successful transmission
        self.update_error_state()
        print(f"{self.name} Sent: {packet} | TEC: {self.TEC} | State: {self.error_state}")

    def receive(self, packet):
        """ Handles incoming CAN messages and detects errors. """
        # Simulate reception error (10% chance)
        if random.random() < 0.1:
            print(f"{self.name} BIT ERROR detected in received message! Sending ERROR FLAG...")
            self.REC += 8  # Bit errors increase REC
            self.send_error_flag()
            return

        self.REC = max(0, self.REC - 1)  # Decrease REC on successful reception
        self.update_error_state()
        print(f"{self.name} Received: {packet} | REC: {self.REC} | State: {self.error_state}")

    def send_error_flag(self):
        """ Sends an error flag based on error state (Active or Passive). """
        if self.error_state == "ERROR-ACTIVE":
            print(f"{self.name} SENDING ACTIVE ERROR FLAG (Dominant bits)")
            self.TEC += 8  # Error-Active flag increases TEC by 8
        elif self.error_state == "ERROR-PASSIVE":
            print(f"{self.name} SENDING PASSIVE ERROR FLAG (Recessive bits)")
            self.TEC += 1  # Passive error flag increases TEC by 1
        self.update_error_state()

    def recover_from_bus_off(self):
        """ Simulates automatic recovery from BUS-OFF mode. """
        if self.is_bus_off():
            print(f"{self.name} attempting recovery from BUS-OFF...")
            time.sleep(2)  # Simulate recovery delay
            self.TEC = 0
            self.REC = 0
            self.error_state = "ERROR-ACTIVE"
            print(f"{self.name} RECOVERED from BUS-OFF!")