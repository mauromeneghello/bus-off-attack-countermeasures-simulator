# CyberPhysical and Iot Security Course - Master Degree in Cybersecurity - UniPd

## First Project: Simulating countermeasures against bus-off attack on CAN bus.

In this project, we explored the Bus-Off attack on the CAN protocol, a critical vulnerability that can force a legitimate
ECUs into a disconnected state through repeated bit error injection. By simulating this attack in a controlled environment,
we were able to reproduce its behavior in detail and analyze its effects on ECU error states. To counter this attack, we analyzed
two existing countermeasures by implementing them in our simplified simulation, proving their effectiveness in protecting
the victim ECUs.

### Defense Mechanisms:

    1. **Countermeasure 1**: based on F1 + F2 detection and, once detection succeeds, reset the victim ECU.
    2. **Countermeasure 2**: defensive attack on the preceding frame, to send the attacker into bus-off state before it does the same to the victim.

### How to Run

Choose **only one** of the following functions in `main.py`, and comment out the others:

#### 1. Basic Bus-Off Attack (no defense)

```python
bus_off_attack()
```

#### 2. Bus-Off Attack with the first countermeasure activated

```python
bus_off_attack_with_countermeasure1()
```

#### 3. Bus-Off Attack with the second countermeasure activated

```python
bus_off_attack_with_countermeasure2()
```

### Credits

Developed as first project for the CyberPhysical and Iot Security Course - Master Degree in Cybersecurity - University of Padua, 2024–2025

**Authors**

- **Mauro Meneghello** — [mauro.meneghello.3@studenti.unipd.it](mailto:mauro.meneghello.3@studenti.unipd.it)
- **Luca Boschiero** — [luca.boschiero@studenti.unipd.it](mailto:luca.boschiero@studenti.unipd.it)
