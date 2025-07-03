import threading
from CANBus import ECU, CanBus, CanPacket

def bus_off_attack():
    print("\n--- SIMULATION: BUS-OFF ATTACK ---\n")

    # Create a simulated CAN bus
    can_bus = CanBus()

    # Create the victim ECU with ID 0x555
    victim = ECU("Victim", can_bus, arbitration_id=0x555)

    # Create the attacker ECU using the same ID to trigger collision
    attacker = ECU("Attacker", can_bus, arbitration_id=0x555)

    # Enable error injection on the attacker ECU
    attacker.can_inject_error = True                                  # turn on attack

    # Function to send the preceding frame to synchronize the victim and attacker transmissions
    def send_preceding_frame():
        print("\n[+] Send Preceding Frame to syncronize")
        # Attacker sends a frame with lower ID (0x001) to win arbitration and prepare timing
        can_bus.send(CanPacket(0x001, [0xAA]), attacker)

    # Recursive function that simulates each step of the attack
    def attack_cycle():
        nonlocal phase

        # Simulate simultaneous frame transmission (victim + attacker)
        print(f"\n[ATT] Attack Cycle (Phase: {phase})")
        victim.send([0xCA, 0xFE])                                  # simulate frame transmission (and retransmission)
        attacker.send([0xCA, 0xFE])                                # simulate frame transmission (and retransmission)

        # transition between phases
        if phase == "PHASE1":
            if victim.TEC >= 128 and attacker.TEC >= 128:
                # If both ECUs reach TEC >= 128, switch to Phase 1to2
                print("\n[->] Transition to PHASE1to2")
                attacker.can_inject_error = False  # do not force errors in this phase
                phase = "PHASE1to2"

        elif phase == "PHASE1to2":
            # Wait for attacker TEC to go back <=127 before starting Phase 2
            if attacker.TEC <= 127:
                print("\n[->] Transition to PHASE2")
                attacker.can_inject_error = False  
                phase = "PHASE2"

        elif phase == "PHASE2":
            # If victim TEC resets to 0, cooldown before resuming attack
            if victim.TEC == 0:
                print("Cooldown after victim reset")
                attacker.can_inject_error = False
                threading.Timer(1.5, lambda: setattr(attacker, "can_inject_error", True)).start()

            # If victim TEC >= 256, victim enters BUS-OFF state and attack ends
            if victim.TEC >= 256:
                print("\n[END] Victim is BUS-OFF! Attack completed.")
                return  # end of attack

        # Print current error counters and state for debugging
        print(f"[Victim] TEC: {victim.TEC} | State: {victim.error_state}")
        print(f"[Attacker] TEC: {attacker.TEC} | State: {attacker.error_state}")

        # Schedule next cycle after 0.5 seconds
        threading.Timer(0.5, attack_cycle).start()

    # Initialize attack phase to PHASE1
    phase = "PHASE1"

    # Start by sending the preceding frame to synchronize timing
    send_preceding_frame()

    # Start the first attack cycle after 0.1 seconds
    threading.Timer(0.1, attack_cycle).start()