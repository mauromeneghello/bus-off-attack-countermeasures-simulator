import threading
import time
from CANBus import ECU, CanBus, CanPacket
import matplotlib.pyplot as plt

tec_rec_log = {
    "time": [],
    "victim_TEC": [],
    "victim_REC": [],
    "attacker_TEC": [],
    "attacker_REC": []
}
start_time = time.time()

def plot_tec_rec():
    # TEC only plot
    plt.figure(figsize=(10, 6))
    plt.plot(tec_rec_log["time"], tec_rec_log["victim_TEC"], label="Victim TEC", color='red')
    plt.plot(tec_rec_log["time"], tec_rec_log["attacker_TEC"], label="Attacker TEC", color='blue')
    
    # Add threshold line at y = 128
    plt.axhline(y=128, color='gray', linestyle='--', linewidth=1)
    plt.text(tec_rec_log["time"][-1] * 0.7, 130, 'TEC 128', color='gray')

    plt.xlabel("Time (s)")
    plt.ylabel("TEC Value")
    plt.title("Transmit Error Counter (TEC) Over Time")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("tec_plot_1.png")
    plt.close()

    # REC only plot
    plt.figure(figsize=(10, 6))
    plt.plot(tec_rec_log["time"], tec_rec_log["victim_REC"], label="Victim REC", linestyle='--', color='pink')
    plt.plot(tec_rec_log["time"], tec_rec_log["attacker_REC"], label="Attacker REC", linestyle='--', color='lightblue')
    plt.xlabel("Time (s)")
    plt.ylabel("REC Value")
    plt.title("Receive Error Counter (REC) Over Time")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("rec_plot_1.png")
    plt.close()

    print("\n[+] Graphs saved: tec_rec_combined.png, tec_plot.png, rec_plot.png")



def bus_off_attack():
    print("\n--- SIMULATION: BUS-OFF ATTACK ---\n")

    can_bus = CanBus()
    victim = ECU("Victim", can_bus, arbitration_id=0x555, enable_defense=True)     # set enable_defense to true to turn on countermeasures
    attacker = ECU("Attacker", can_bus, arbitration_id=0x555)
    attacker.can_inject_error = True  # turn on attack

    def send_preceding_frame():
        print("\n[+] Send Preceding Frame to syncronize")
        can_bus.send(CanPacket(0x001, [0xAA]), attacker)

    def attack_cycle():
        nonlocal phase
        # send frame in the same exact moment
        print(f"\n[ATT] Attack Cycle (Phase: {phase})")
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
                attacker.can_inject_error = False  # restart forcing errors
                phase = "PHASE2"
                victim.send([0xCA, 0xFE], retransmission=True)
        elif phase == "PHASE2":
            current_time = time.time() - start_time
            tec_rec_log["time"].append(current_time)
            tec_rec_log["victim_TEC"].append(victim.TEC)
            tec_rec_log["victim_REC"].append(victim.REC)
            tec_rec_log["attacker_TEC"].append(attacker.TEC)
            tec_rec_log["attacker_REC"].append(attacker.REC)
            victim.send([0xCA, 0xFE], retransmission=True)
            # log immediately to capture the TEC -1
            current_time = time.time() - start_time
            tec_rec_log["time"].append(current_time)
            tec_rec_log["victim_TEC"].append(victim.TEC)
            tec_rec_log["victim_REC"].append(victim.REC)
            tec_rec_log["attacker_TEC"].append(attacker.TEC)
            tec_rec_log["attacker_REC"].append(attacker.REC)
            if victim.TEC == 0:
                print("Cooldown after victim reset")
                attacker.can_inject_error = False
                threading.Timer(1.5, lambda: setattr(attacker, "can_inject_error", True)).start()
            if victim.TEC >= 256:
                print("\n[END] Victim is BUS-OFF! Attack completed.")
                plot_tec_rec()
                return  # end of attack
            if attacker.TEC >= 256:
                print("\n[END] Attacker is BUS-OFF!.")
                plot_tec_rec()
                return  # end of attack

        # states
        print(f"[Victim] TEC: {victim.TEC} | State: {victim.error_state}")
        print(f"[Attacker] TEC: {attacker.TEC} | State: {attacker.error_state}")

        # Log TEC/REC
        current_time = time.time() - start_time
        tec_rec_log["time"].append(current_time)
        tec_rec_log["victim_TEC"].append(victim.TEC)
        tec_rec_log["victim_REC"].append(victim.REC)
        tec_rec_log["attacker_TEC"].append(attacker.TEC)
        tec_rec_log["attacker_REC"].append(attacker.REC)


        # next cycle
        threading.Timer(0.5, attack_cycle).start()

    phase = "PHASE1"
    send_preceding_frame()
    threading.Timer(0.1, attack_cycle).start()


if __name__ == "__main__":
    bus_off_attack()