"""
標準化訓練腳本
用於Docker容器內執行AI訓練任務
"""
import argparse
import time
import logging
import os
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def train(epochs: int, batch_size: int, learning_rate: float, log_dir: str = "/logs"):
    """
    執行訓練任務
    
    Args:
        epochs: 訓練輪數
        batch_size: 批次大小
        learning_rate: 學習率
        log_dir: 日志目錄
    """
    logger.info("=" * 60)
    logger.info("AI Training Started")
    logger.info("Epochs: %s | Batch: %s | LR: %s", epochs, batch_size, learning_rate)
    logger.info("=" * 60)
    
    os.makedirs(log_dir, exist_ok=True)
    
    for epoch in range(1, epochs + 1):
        logger.info("Epoch %s/%s started", epoch, epochs)
        
        for step in range(1, 11):
            loss = 1.0 / (epoch * step) + 0.1
            accuracy = min(0.95, 0.5 + epoch * 0.1 + step * 0.01)
            logger.info("Epoch %s/%s, Step %s/10 - Loss: %.4f, Accuracy: %.4f",
                        epoch, epochs, step, loss, accuracy)
            time.sleep(0.5)
        
        logger.info("Epoch %s/%s completed", epoch, epochs)
        checkpoint_path = os.path.join(log_dir, "checkpoint_epoch_%s.pth" % epoch)
        with open(checkpoint_path, 'w') as f:
            f.write("Checkpoint at epoch %s\n" % epoch)
        logger.info("Checkpoint saved: %s", checkpoint_path)
    
    logger.info("=" * 60)
    logger.info("Training Completed Successfully")
    logger.info("=" * 60)
    
    result_path = os.path.join(log_dir, "training_result.txt")
    with open(result_path, 'w') as f:
        f.write("Training completed at %s\n" % datetime.now())
        f.write("Total epochs: %s\n" % epochs)
        f.write("Final accuracy: %.4f\n" % min(0.95, 0.5 + epochs * 0.1))
    logger.info("Training result saved: %s", result_path)


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description="AI Training Script")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--learning-rate", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--log-dir", type=str, default="/logs", help="Log directory")
    
    args = parser.parse_args()
    
    try:
        train(
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.learning_rate,
            log_dir=args.log_dir
        )
        exit(0)
    except Exception as e:
        logger.error("Training failed: %s", e, exc_info=True)
        exit(1)


if __name__ == "__main__":
    main()
