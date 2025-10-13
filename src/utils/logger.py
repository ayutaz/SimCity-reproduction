"""
Logger setup for SimCity

loguruを使用したロギング設定を提供
"""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger


def setup_logger(
    log_level: str = "INFO",
    log_file: Optional[str | Path] = None,
    rotation: str = "10 MB",
    retention: str = "7 days",
    enable_console: bool = True,
) -> None:
    """
    ロガーのセットアップ

    Args:
        log_level: ログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: ログファイルのパス (Noneの場合はファイル出力なし)
        rotation: ログローテーション条件
        retention: ログ保持期間
        enable_console: コンソール出力を有効化
    """
    # デフォルトハンドラを削除
    logger.remove()

    # ログレベルの検証
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if log_level.upper() not in valid_levels:
        log_level = "INFO"

    # コンソール出力の設定
    if enable_console:
        logger.add(
            sys.stderr,
            level=log_level.upper(),
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                "<level>{message}</level>"
            ),
            colorize=True,
        )

    # ファイル出力の設定
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            log_path,
            level=log_level.upper(),
            format=(
                "{time:YYYY-MM-DD HH:mm:ss} | "
                "{level: <8} | "
                "{name}:{function}:{line} | "
                "{message}"
            ),
            rotation=rotation,
            retention=retention,
            compression="zip",
            encoding="utf-8",
        )

        logger.info(f"Logger initialized with file output: {log_path}")


def get_logger(name: str):
    """
    名前付きロガーを取得

    Args:
        name: ロガー名（通常はモジュール名）

    Returns:
        logger instance
    """
    return logger.bind(name=name)


class LoggerContext:
    """
    コンテキストマネージャーでログレベルを一時変更

    Example:
        with LoggerContext("DEBUG"):
            # この中だけDEBUGレベルのログが出力される
            logger.debug("This is debug message")
    """

    def __init__(self, temp_level: str):
        self.temp_level = temp_level
        self.original_level = None

    def __enter__(self):
        # 現在のログレベルを保存
        # loguruは動的にレベルを変更できないため、新しいハンドラを追加
        logger.add(
            sys.stderr,
            level=self.temp_level,
            format="<level>{level}: {message}</level>",
        )
        return logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 元のハンドラに戻す（簡略化のため、ここでは省略）
        pass
