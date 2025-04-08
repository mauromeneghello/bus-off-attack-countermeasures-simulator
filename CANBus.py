import random
import time
import threading

class CanPacket:
    """ Represents a CAN packet with an ID, data, and timestamp. """
    def __init__(self, arbitration_id, data):
        self.arbitration_id = arbitration_id
        self.data = data
        self.timestamp = time.time()

    def __repr__(self):
        return f"CAN Packet(ID={hex(self.arbitration_id)}, Data={self.data}, Time={self.timestamp:.3f})"


class CanBus:
    """ Simulates a CAN bus where ECUs send and receive messages with error handling. """
    def __init__(self):
        self.listeners = []
        self.recent_successful_ids = {}  # {arbitration_id: ecu_name}

    def register_ecu(self, ecu):
        self.listeners.append(ecu)

    def send(self, packet, sender_ecu):
        if sender_ecu.is_bus_off():
            print(f"{sender_ecu.name} is in BUS-OFF! Cannot send: {packet}")
            return

        print(f"CAN Bus Transmitting: {packet}")

        for ecu in self.listeners:
            if ecu != sender_ecu:
                ecu.receive(packet)

        self.recent_successful_ids[packet.arbitration_id] = sender_ecu.name
        self.arbitrate(packet, sender_ecu)

    def arbitrate(self, packet, sender_ecu):
        print(f"Arbitration in progress for {sender_ecu.name} with ID {hex(packet.arbitration_id)}")

        competing_ecus = [ecu for ecu in self.listeners if ecu != sender_ecu and not ecu.is_bus_off()]
        competing_ecus.append(sender_ecu)
        competing_ecus.sort(key=lambda ecu: ecu.arbitration_id)

        winner_ecu = competing_ecus[0]
        print(f"Arbitration Winner: {winner_ecu.name} with ID {hex(winner_ecu.arbitration_id)}")

        for ecu in self.listeners:
            if ecu != winner_ecu:
                ecu.receive(packet)

        winner_ecu.TEC = max(0, winner_ecu.TEC - 1)
        winner_ecu.consecutive_errors = 0
        winner_ecu.update_error_state()

        print(f"{winner_ecu.name} Sent: {packet} | TEC: {winner_ecu.TEC} | State: {winner_ecu.error_state}")


class ECU:
    def __init__(self, name, can_bus, arbitration_id, enable_defense=True):
        self.name = name
        self.can_bus = can_bus
        self.arbitration_id = arbitration_id
        self.enable_defense = enable_defense

        self.can_bus.register_ecu(self)

        self.TEC = 0
        self.REC = 0
        self.error_state = "ERROR-ACTIVE"

        self.consecutive_errors = 0

    def update_error_state(self):
        if self.TEC >= 256:
            self.error_state = "BUS-OFF"
            print(f"{self.name} ENTERED BUS-OFF MODE!")
        elif self.TEC >= 128 or self.REC >= 128:
            self.error_state = "ERROR-PASSIVE"
        else:
            self.error_state = "ERROR-ACTIVE"

    def is_bus_off(self):
        return self.error_state == "BUS-OFF"

    def send(self, data):
        if self.is_bus_off():
            print(f"{self.name} is in BUS-OFF! Cannot send.")
            return

        packet = CanPacket(self.arbitration_id, data)

        if random.random() < 0.1:
            print(f"{self.name} BIT ERROR detected! Sending ERROR FLAG...")
            self.send_error_flag(packet.arbitration_id)
            return

        self.can_bus.send(packet, self)
        self.TEC = max(0, self.TEC - 1)
        self.consecutive_errors = 0
        self.update_error_state()

        print(f"{self.name} Sent: {packet} | TEC: {self.TEC} | State: {self.error_state}")

    def receive(self, packet):
        if random.random() < 0.1:
            print(f"{self.name} BIT ERROR detected in received message! Sending ERROR FLAG...")
            self.REC += 8
            self.send_error_flag(packet.arbitration_id)
            return

        self.REC = max(0, self.REC - 1)
        self.update_error_state()
        print(f"{self.name} Received: {packet} | REC: {self.REC} | State: {self.error_state}")

    def send_error_flag(self, failed_id=None):
        self.consecutive_errors += 1

        if self.error_state == "ERROR-ACTIVE":
            print(f"{self.name} SENDING ACTIVE ERROR FLAG (Dominant bits)")
            self.TEC += 8
        elif self.error_state == "ERROR-PASSIVE":
            print(f"{self.name} SENDING PASSIVE ERROR FLAG (Recessive bits)")
            self.TEC += 1

            if self.consecutive_errors >= 16 and failed_id is not None:
                sender = self.can_bus.recent_successful_ids.get(failed_id)
                if sender and sender != self.name:
                    print(f"🛡 {self.name} DETECTED BUS-OFF ATTACK! F1+F2 matched.")
                    if self.enable_defense:
                        print(f"🛡 {self.name} Difesa ATTIVA → Reset ECU.")
                        self.recover_from_bus_off()
                    else:
                        print(f"🛡 {self.name} Difesa DISATTIVATA → Nessun recupero.")

        self.update_error_state()

    def recover_from_bus_off(self):
        if self.is_bus_off() or self.error_state == "ERROR-PASSIVE":
            print(f"{self.name} attempting recovery...")
            time.sleep(1)
            self.TEC = 0
            self.REC = 0
            self.error_state = "ERROR-ACTIVE"
            self.consecutive_errors = 0
            print(f"{self.name} RECOVERED from BUS-OFF/ERROR-PASSIVE!")



def main_attacco_senza_difesa():
    print("▶️ INIZIO: Attacco con difesa DISATTIVATA")
    random.seed(42)

    bus = CanBus()
    ecu_a = ECU("ECU_A", bus, arbitration_id=0x100, enable_defense=False)
    ecu_attacker = ECU("ECU_Attacker", bus, arbitration_id=0x100)

    def victim_behavior():
        print("🚗 ECU_A: trasmissione legittima...")
        for i in range(5):
            ecu_a.send([0x01, i])
            time.sleep(0.5)

    def attacker_behavior():
        print("🔓 ECU_Attacker: inizio spoofing...")
        time.sleep(1.5)
        for i in range(20):
            ecu_attacker.send([0xFF, i])
            time.sleep(0.3)

    t1 = threading.Thread(target=victim_behavior)
    t2 = threading.Thread(target=attacker_behavior)

    t1.start()
    t2.start()
    t1.join()
    t2.join()
    print("❌ Fine attacco senza difesa\n")



def main_attacco_con_difesa():
    print("▶️ INIZIO: Attacco con difesa ATTIVATA")
    random.seed(42)

    bus = CanBus()
    ecu_a = ECU("ECU_A", bus, arbitration_id=0x100, enable_defense=True)
    ecu_attacker = ECU("ECU_Attacker", bus, arbitration_id=0x100)

    def victim_behavior():
        print("🚗 ECU_A: trasmissione legittima...")
        for i in range(5):
            ecu_a.send([0x01, i])
            time.sleep(0.5)

    def attacker_behavior():
        print("🔓 ECU_Attacker: inizio spoofing...")
        time.sleep(1.5)
        for i in range(20):
            ecu_attacker.send([0xFF, i])
            time.sleep(0.3)

    t1 = threading.Thread(target=victim_behavior)
    t2 = threading.Thread(target=attacker_behavior)

    t1.start()
    t2.start()
    t1.join()
    t2.join()
    print("✅ Fine attacco con difesa\n")



if __name__ == "__main__":
    
    main_attacco_senza_difesa()
    time.sleep(2)
    print("\n" + "="*50 + "\n")
    # main_attacco_con_difesa()

