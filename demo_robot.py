"""EKS Demo — Robot Navigation with DeepSeek Coder + Laya"""
import time, random
from eks.eks import EKS

SCENARIOS = [
    "Front: 45cm obstacle. Left: 120cm. Right: 80cm. Battery: 87%. Terrain: smooth.",
    "Narrow corridor. Front: 30cm. Left: 15cm wall. Right: 18cm wall. Battery: 85%.",
    "Open space. Front: 300cm. Left: 280cm. Right: 310cm. Battery: 83%.",
    "Obstacle ahead 20cm. Left blocked 10cm. Right: 90cm open. Battery: 81%.",
    "T-junction. Front: 200cm. Left: 150cm. Right: 170cm. Battery: 78%.",
    "Dead-end. Front: 15cm. Left: 8cm. Right: 12cm. Battery: 75%.",
    "Rough terrain. Vibration high. Front: 100cm clear. Battery: 72%.",
    "Battery low! Front: 200cm clear. Charging station: left. Battery: 18%.",
    "High-speed corridor. Front: 400cm. Left: 400cm. Right: 400cm. Battery: 68%.",
    "Unknown terrain. Sensor noise. Front: unclear. Battery: 65%.",
    "Wall ahead 10cm. Left open 200cm. Right open 150cm. Battery: 60%.",
    "Clear path to target. Front: 350cm. All clear. Battery: 55%.",
]

def main():
    print("=" * 60)
    print("  EKS — Robot Navigation Demo")
    print("  LLM : DeepSeek Coder V2 Lite (port 8001)")
    print("  Exec: Laya MLX (typed decisions)")
    print("=" * 60 + "\n")

    eks = EKS(
        domain="robot_navigation",
        description=(
            "Mobile robot in indoor warehouse. Sensors: ultrasonic front/left/right, "
            "battery level, terrain roughness. Needs: direction, speed, safety decisions."
        ),
        laya_model="aac6fef/laya-mlx",
        llm_url="http://localhost:8001/v1",
        storage="./eks_core",
    )

    eks.status()
    print("🤖 Running navigation loop (20 ticks)...\n")

    for i in range(20):
        inp = random.choice(SCENARIOS)
        print(f"[Tick {i+1:02d}] {inp}")

        t0 = time.perf_counter()
        answers = eks.decide(inp)
        ms = (time.perf_counter() - t0) * 1000

        if answers:
            parts = []
            for k, v in answers.items():
                ans  = v.get("answer", "?")
                conf = v.get("confidence", 0)
                parts.append(f"{k}={ans}({conf:.2f})")
            print(f"  → [{ms:.0f}ms] {' | '.join(parts)}")
        else:
            print(f"  → [{ms:.0f}ms] (no answer)")
        time.sleep(0.2)

    print()
    eks.status()

if __name__ == "__main__":
    main()
