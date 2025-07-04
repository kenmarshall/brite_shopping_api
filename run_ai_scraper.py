from app.agents.ai_scraper_agent import run
import sys

if __name__ == "__main__":
    task = "Gather grocery products sold in Jamaica" if len(sys.argv) == 1 else " ".join(sys.argv[1:])
    run(task)
