import random
import time
from collections import deque

class CanPacket:
    def __init__(self, ID, data):
        self.sof = 0  # Start of Frame: Dominant bit (0)
        self.ID = ID  # Frame identifier
        self.dlc = len(data)  # Data Length Code (DLC) from 0 to 8 bytes
        self.data = data  # Data payload (up to 8 bytes)
        self.rtr = 0  # Remote Transmission Request: 0 means sending data
        self.crc = '101010101010101'  # Example CRC (placeholder, 15 bits)
        self.ack = [1, 1]  # ACK field, placeholder for 2 recessive bits
        self.eof = [1] * 7  # End of Frame: 7 recessive bits (EOF)

    def to_bits(self):
        """ Serializes the CAN packet to a list of bits for transmission """
        bits = []

        # 1. Start of Frame (SoF)
        bits.append(0)  # Dominant bit (SoF)

        # 2. 11-bit Identifier (ID)
        id_bits = format(self.ID, '011b')
        bits.extend(int(b) for b in id_bits)

        # 3. Control Field: 
        #    - RTR: 1 bit
        #    - DLC: 4 bits
        control_bits = [self.rtr]  # RTR bit
        control_bits.extend(int(b) for b in format(self.dlc, '04b'))  # DLC (4 bits)
        bits.extend(control_bits)

        # 4. Data Field: Convert each byte of data to 8 bits
        for byte in self.data:
            byte_bits = format(byte, '08b')
            bits.extend(int(b) for b in byte_bits)

        # 5. CRC Field: 15 bits (this is just a placeholder CRC for now)
        crc_bits = self.crc  # Placeholder CRC (15 bits)
        bits.extend(int(b) for b in crc_bits)

        # 6. ACK Slot: 2 recessive bits (placeholder, 1 for delimiter)
        bits.extend(self.ack)

        # 7. End of Frame (EOF): 7 recessive bits
        bits.extend(self.eof)

        return bits

    def __repr__(self):
        return f"CAN Packet(ID={hex(self.ID)}, Data={self.data}, DLC={self.dlc})"


class CanBus:
    """ Simulates a CAN bus where ECUs send and receive messages with error handling. """
    def __init__(self):
        self.listeners = []  # List of ECUs listening to the bus
        self.idle = True
        self.send_queue = deque()  # Queue of (packet, sender_ecu)

    def register_ecu(self, ecu):
        """ Registers an ECU to listen on the CAN bus. """
        self.listeners.append(ecu)

    def send(self, packet, sender_ecu):
        """ Handles send requests: send immediately if idle, else queue it. """
        if sender_ecu.is_bus_off():
            print(f"{sender_ecu.name} is in BUS-OFF! Cannot send: {packet}")
            return

        if not self.idle:
            print(f"{sender_ecu.name} wants to send, but bus is BUSY. Queuing packet.")
            self.send_queue.append((packet, sender_ecu))
            return

        # Start arbitration when the bus is idle
        self._start_arbitration()

    def _start_arbitration(self):
        """ Start the arbitration process if multiple ECUs are queued. """
        if self.send_queue:
            print("Starting arbitration...")

            # Check competing ECUs (those waiting in the queue)
            competing_ecus = [(packet, ecu) for packet, ecu in self.send_queue]
            competing_ecus.sort(key=lambda item: item[0].ID)  # Sort by arbitration ID (lowest wins)

            # The first ECU in the sorted list is the winner
            winner_packet, winner_ecu = competing_ecus[0]
            print(f"Arbitration Winner: {winner_ecu.name} with ID {hex(winner_packet.ID)}")

            # Transmit the winning ECU's packet
            self._transmit(winner_packet, winner_ecu)

            # Remove only the winning ECU from the queue
            self.send_queue = deque([item for item in competing_ecus[1:]])
            
            # If there are any ECUs left, process the next message
            self._process_queue()

    def _transmit(self, packet, sender_ecu):
        """ Internal method to transmit a packet bit by bit. """
        self.idle = False
        bits = packet.to_bits()

        print(f"\n{sender_ecu.name} STARTS transmitting bit by bit:")
        for idx, bit in enumerate(bits):
            print(f" Bit {idx:03}: {bit}")
            time.sleep(0.001)  # Simulated bit time

        print(f"{sender_ecu.name} Transmission COMPLETE.\n")

        # Notify all other ECUs
        for ecu in self.listeners:
            if ecu != sender_ecu:
                ecu.receive(packet)

        self.idle = True
        self._process_queue()

    def _process_queue(self):
        """ Process the next message in the queue if available. """
        if self.send_queue and self.idle:
            next_packet, next_sender = self.send_queue.popleft()
            print(f"Dequeued message from {next_sender.name}, preparing to send...")
            self._start_arbitration()  # Call arbitration again after dequeuing

    def send_error_flag(self, error_flag_bits, sender_ecu):
        """ Simulates sending an error flag on the CAN bus. """
        print(f"CAN BUS: ERROR FLAG sent by {sender_ecu.name} -> {''.join(map(str, error_flag_bits))}")
        for ecu in self.listeners:
            if ecu != sender_ecu:
                ecu.on_error_detected()


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
        """ Sends an error flag and notifies the bus and other ECUs. """
        if self.error_state == "ERROR-ACTIVE":
            print(f"{self.name} SENDING ACTIVE ERROR FLAG (Dominant bits)")
            self.TEC += 8
            error_flag = [0] * 6  # 6 dominant bits
        elif self.error_state == "ERROR-PASSIVE":
            print(f"{self.name} SENDING PASSIVE ERROR FLAG (Recessive bits)")
            self.TEC += 1
            error_flag = [1] * 6  # 6 recessive bits
        else:
            return

        self.update_error_state()

        # Send error flag to the bus
        self.can_bus.send_error_flag(error_flag, sender_ecu=self)

    def recover_from_bus_off(self):
        """ Simulates automatic recovery from BUS-OFF mode. """
        if self.is_bus_off():
            print(f"{self.name} attempting recovery from BUS-OFF...")
            time.sleep(2)  # Simulate recovery delay
            self.TEC = 0
            self.REC = 0
            self.error_state = "ERROR-ACTIVE"
            print(f"{self.name} RECOVERED from BUS-OFF!")
    
    def on_error_detected(self):
        """ React to an error flag on the bus (e.g., increase REC). """
        print(f"{self.name} detected ERROR FLAG on bus! Incrementing REC.")
        self.REC += 1  # or more, depending on how severe you want the simulation
        self.update_error_state()