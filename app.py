"""
SimCity Dashboard Application

Streamlitダッシュボードのエントリーポイント

使い方:
    streamlit run app.py
    または
    uv run streamlit run app.py
"""

from src.visualization.dashboard import main

if __name__ == "__main__":
    main()
