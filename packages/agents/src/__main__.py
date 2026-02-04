"""패키지를 python -m src 로 실행 가능하게 합니다."""

import sys

from src.cli import main

if __name__ == "__main__":
    sys.exit(main())
