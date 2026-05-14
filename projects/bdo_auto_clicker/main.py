
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from auto_clicker import BDOAutoClicker


def main() -> None:
    clicker = BDOAutoClicker(check_interval=0.1)
    clicker.run()


if __name__ == "__main__":
    main()
