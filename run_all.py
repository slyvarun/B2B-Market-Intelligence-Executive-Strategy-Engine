import sys
import time
from module1_data_collector import main as run_module1
from module2_scoring_engine import main as run_module2
from module3_content_engine import main as run_module3
from module4_feedback_engine import main as run_module4


def run_entire_pipeline():
    print("=" * 80)
    print("Starting B2B Market Intelligence Pipeline...")
    print("=" * 80)

    start_time = time.time()

    print("\n[Step 1] Ingesting Market Signals...")
    run_module1()
    time.sleep(1)

    print("\n[Step 2] Scoring Opportunities...")
    run_module2()
    time.sleep(1)

    print("\n[Step 3] Structuring Executive Content Strategy...")
    run_module3()
    time.sleep(1)

    print("\n[Step 4] Analyzing Business Performance & Feedback...")
    run_module4()

    elapsed = round(time.time() - start_time, 2)

    print("\n" + "=" * 80)
    print(f"Pipeline executed successfully in {elapsed}s.")
    print("Database updated: market_signals.db")
    print("=" * 80)


if __name__ == "__main__":
    run_entire_pipeline()
