import threading
from CANBus import ECU, CanBus, CanPacket

def bus_off_attack_with_countermeasure1():
    print("\n--- SIMULATION: BUS-OFF ATTACK ---\n")

    can_bus = CanBus()
    victim = ECU("Victim", can_bus, arbitration_id=0x555, enable_defense=True)              # victim ECU
    attacker = ECU("Attacker", can_bus, arbitration_id=0x555)          # attacker ECU
    attacker.can_inject_error = True                                   # turn on attack

    def send_preceding_frame():                                        # simulate sending preceding frame to syncronize victim and attacker frames
        print("\n[+] Send Preceding Frame to syncronize")
        can_bus.send(CanPacket(0x001, [0xAA]), attacker)

    def attack_cycle():
        nonlocal phase
        # send frame in the same exact moment
        print(f"\n[ATT] Attack Cycle (Phase: {phase})")
        victim.send([0xCA, 0xFE])                                  # simulate frame transmission (and retransmission)
        attacker.send([0xCA, 0xFE])                                # simulate frame transmission (and retransmission)

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
            if attacker.TEC >= 256:
                print("\n[END] Attacker is BUS-OFF! Defense successful.")
                return  # end of attack

        # states
        print(f"[Victim] TEC: {victim.TEC} | State: {victim.error_state}")
        print(f"[Attacker] TEC: {attacker.TEC} | State: {attacker.error_state}")

        # next cycle
        threading.Timer(0.5, attack_cycle).start()

    phase = "PHASE1"
    send_preceding_frame()
    threading.Timer(0.1, attack_cycle).start()