import threading
import time
from CANBus import ECU, CanBus, CanPacket

def bus_off_attack():
    print("\n--- SIMULATION: BUS-OFF ATTACK ---\n")

    can_bus = CanBus()
    victim = ECU("Victim", can_bus, arbitration_id=0x555) 
    attacker = ECU("Attacker", can_bus, arbitration_id=0x555)             # attacker targets victim frame
    guardian_ecu = ECU("GuardianECU", can_bus, arbitration_id=0x554)      # guardian targets attacker preceding frame

    attacker.can_inject_error = True  # turn on attack
    guardian_ecu.can_inject_error = True

    def send_preceding_frame(sender: ECU, id):
        print(f"\n[+] {sender.name} send Preceding Frame to syncronize")
        sender.send([0xAA], preceding_frame=True)

    def attack_cycle(victim: ECU, attacker: ECU):
        nonlocal phase
        # send frame in the same exact moment
        print(f"\n[ATT] Attack Cycle (Phase: {phase})")

        if (victim.name == 'Attacker'):
            victim.send([0xCA, 0xFE], preceding_frame=True)             # to simulate retransmission of the preceding frame by the attacker
        else:
            victim.send([0xCA, 0xFE])

        attacker.send([0xCA, 0xFE])          

        # transition between phases
        if phase == "PHASE1":
            if victim.TEC >= 128 and attacker.TEC >= 128:
                print("\n[->] Transition to PHASE1to2")
                attacker.can_inject_error = False  # do not force errors in this phase
                phase = "PHASE1to2"
        elif phase == "PHASE1to2":
            if attacker.TEC <= 127:
                print("\n[->] Transition to PHASE2")
                attacker.can_inject_error = False  
                phase = "PHASE2"
        elif phase == "PHASE2":
            if victim.TEC == 0:
                print("Cooldown after victim reset")
                attacker.can_inject_error = False
                threading.Timer(1.5, lambda: setattr(attacker, "can_inject_error", True)).start()
            if victim.TEC >= 256:
                print("\n[END] Victim is BUS-OFF! Attack completed.")
                return  # end of attack

        # states
        print(f"[Victim : {victim.name}] TEC: {victim.TEC} | State: {victim.error_state}")
        print(f"[Attacker: {attacker.name}] TEC: {attacker.TEC} | State: {attacker.error_state}")

        # next cycle
        threading.Timer(0.5, attack_cycle(victim, attacker)).start()

    phase = "PHASE1"
    

    # once detected the preceding frame of the attacker, start another bus off against it
    send_preceding_frame(guardian_ecu, 0x553)     # guardian sends preceding frame
        
    threading.Timer(0.1, attack_cycle(victim=attacker, attacker=guardian_ecu)).start()
    threading.Timer(0.1, attack_cycle(victim=victim, attacker=attacker)).start()


if __name__ == "__main__":
    bus_off_attack()