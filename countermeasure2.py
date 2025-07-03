import threading
import time
from CANBus import ECU, CanBus

def bus_off_attack_with_countermeasure2():
    print("\n--- SIMULATION: BUS-OFF ATTACK ---\n")

    # Create a simulated CAN bus
    can_bus = CanBus()

    # Create the victim ECU with ID 0x555
    victim = ECU("Victim", can_bus, arbitration_id=0x555)

    # Create the attacker ECU using the same ID to trigger collision                  
    attacker = ECU("Attacker", can_bus, arbitration_id=0x555)    

    # Create the Guardian ECU to target attacker's preceding frame         
    guardian_ecu = ECU("GuardianECU", can_bus, arbitration_id=0x554) 

    # Enable error injection on the attacker ECU and on the Guardian ECU
    attacker.can_inject_error = True 
    guardian_ecu.can_inject_error = True

    # Function to send the preceding frame to synchronize the victim and attacker transmissions  
    def send_preceding_frame(sender: ECU, id): 
        # ECU who wants to attack sends a frame to win arbitration and prepare timing                                
        print(f"\n[+] {sender.name} send Preceding Frame to syncronize")
        sender.send([0xAA], preceding_frame=True)


    # Recursive function that simulates each step of the attack
    def attack_cycle(victim: ECU, attacker: ECU):
        nonlocal phase

        # Simulate simultaneous frame transmission
        print(f"\n[ATT] Attack Cycle (Phase: {phase})")

        if (victim.name == 'Attacker'):
            victim.send([0xCA, 0xFE], preceding_frame=True)             # to simulate retransmission of the preceding frame by the attacker
        else:
            victim.send([0xCA, 0xFE])                                   # simulate retransmission of the victim frame

        attacker.send([0xCA, 0xFE])                                     # simulate retransmission of the attacker frame

        # transition between phases
        if phase == "PHASE1":
            # If both ECUs reach TEC >= 128, switch to Phase 1to2
            if victim.TEC >= 128 and attacker.TEC >= 128:
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
            # If victim TEC >= 256, victim enters BUS-OFF state and attack ends successfully
            if victim.TEC >= 256:
                print("\n[END] Victim is BUS-OFF! Attack completed.")
                return  # end of attack
            
            # If attacket TEC >= 256, attacker enters BUS-OFF state and attack ends failing
            if attacker.TEC >= 256:
                print("\n[END] Attacker is BUS-OFF! Defense successful.")
                return  # end of attack

        # Print current error counters and state for debugging
        print(f"[Victim : {victim.name}] TEC: {victim.TEC} | State: {victim.error_state}")
        print(f"[Attacker: {attacker.name}] TEC: {attacker.TEC} | State: {attacker.error_state}")

        # Schedule next cycle after 0.5 seconds
        threading.Timer(0.5, attack_cycle(victim, attacker)).start()

    # Initialize attack phase to PHASE1
    phase = "PHASE1"

    # once detected the preceding frame of the attacker, start another bus off against it
    send_preceding_frame(guardian_ecu, 0x553)     # guardian sends preceding frame
    
    # Start the attack cycles (attacker vs victim and Guardian ECU vs attacker) after 0.1 seconds
    threading.Timer(0.1, attack_cycle(victim=attacker, attacker=guardian_ecu)).start()
    threading.Timer(0.1, attack_cycle(victim=victim, attacker=attacker)).start()