import threading
import time
from CANBus import ECU, CanBus, CanPacket

# # ECU malevola che forza errori agli altri
# class Attacker(ECU):
#     def receive(self, packet):
#         print(f"{self.name} finge un errore ogni volta! Invio flag errore.")
#         self.send_error_flag()

#     def send_preceding_frame(self):
#         """ Sends a preceding frame with low ID to manipulate arbitration timing """
#         preceding_id = 0x000  # The lowest possible ID to win arbitration
#         preceding_packet = CanPacket(preceding_id, [0xAA])  # Arbitrary data
#         print(f"{self.name} sending PRECEDING FRAME with ID={hex(preceding_id)}")
#         self.can_bus.send(preceding_packet, self)

def bus_off_attack():
    print("\n--- SIMULAZIONE: ATTACCO BUS-OFF (senza difesa) ---\n")

    can_bus = CanBus()
    victim = ECU("Victim", can_bus, arbitration_id=0x555)
    attacker = ECU("Attacker", can_bus, arbitration_id=0x555)
    attacker.can_inject_error = True  # abilita attacco

    def send_preceding_frame():
        print("\n[+] Preceding Frame per sincronizzazione")
        can_bus.send(CanPacket(0x001, [0xAA]), attacker)

    def attack_cycle():
        nonlocal phase
        # Invia frame contemporaneamente
        print(f"\n[⚡] Ciclo attacco (Phase: {phase})")
        victim.send([0xCA, 0xFE])
        attacker.send([0xCA, 0xFE])

        # Condizioni di transizione fasi
        if phase == "PHASE1":
            if victim.TEC >= 128 and attacker.TEC >= 128:
                print("\n[→] Transition to PHASE1to2")
                attacker.can_inject_error = False  # non forza errore in questa fase
                phase = "PHASE1to2"
        elif phase == "PHASE1to2":
            if attacker.TEC <= 127:
                print("\n[→] Transition to PHASE2")
                attacker.can_inject_error = True  # torna a forzare errori
                phase = "PHASE2"
        elif phase == "PHASE2":
            if victim.TEC >= 256:
                print("\n[🚨] Victim is BUS-OFF! Attacco completato.")
                return  # Fine attacco

        # Stampa stati
        print(f"[Victim] TEC: {victim.TEC} | State: {victim.error_state}")
        print(f"[Attacker] TEC: {attacker.TEC} | State: {attacker.error_state}")

        # Prossimo ciclo
        threading.Timer(0.5, attack_cycle).start()

    phase = "PHASE1"
    send_preceding_frame()
    threading.Timer(0.1, attack_cycle).start()


if __name__ == "__main__":
    bus_off_attack()