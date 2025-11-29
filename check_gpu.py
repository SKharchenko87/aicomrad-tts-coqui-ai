#!/usr/bin/env python3
"""
Скрипт для проверки доступности GPU и CUDA в контейнере.
"""
import sys

def check_gpu():
    print("="*60)
    print("GPU/CUDA Verification Script")
    print("="*60)
    
    # Проверка PyTorch
    try:
        import torch
        print(f"\n✓ PyTorch version: {torch.__version__}")
    except ImportError:
        print("\n❌ PyTorch not installed")
        return False
    
    # Проверка CUDA
    cuda_available = torch.cuda.is_available()
    print(f"✓ CUDA available: {cuda_available}")
    
    if cuda_available:
        print(f"✓ CUDA version: {torch.version.cuda}")
        print(f"✓ cuDNN version: {torch.backends.cudnn.version()}")
        print(f"✓ Number of GPUs: {torch.cuda.device_count()}")
        
        for i in range(torch.cuda.device_count()):
            print(f"\n  GPU {i}:")
            print(f"    Name: {torch.cuda.get_device_name(i)}")
            print(f"    Compute Capability: {torch.cuda.get_device_capability(i)}")
            
            # Память
            total_memory = torch.cuda.get_device_properties(i).total_memory / 1024**3
            print(f"    Total Memory: {total_memory:.2f} GB")
            
            # Тест выделения памяти
            try:
                test_tensor = torch.randn(1000, 1000).cuda(i)
                allocated = torch.cuda.memory_allocated(i) / 1024**3
                print(f"    Memory Allocated (test): {allocated:.4f} GB")
                del test_tensor
                torch.cuda.empty_cache()
                print(f"    ✓ GPU {i} is functional")
            except Exception as e:
                print(f"    ❌ Error testing GPU {i}: {e}")
    else:
        print("\n⚠️  CUDA not available - running in CPU mode")
        print("   Possible reasons:")
        print("   - No NVIDIA GPU detected")
        print("   - NVIDIA drivers not installed")
        print("   - Docker not started with --gpus flag")
        print("   - PyTorch CPU-only version installed")
    
    # Проверка TTS
    print("\n" + "="*60)
    print("TTS Library Check")
    print("="*60)
    
    try:
        from TTS.api import TTS
        print("✓ TTS library imported successfully")
        
        # Проверка, что TTS может использовать GPU
        if cuda_available:
            print("✓ TTS can use GPU acceleration")
        else:
            print("⚠️  TTS will run on CPU")
            
    except ImportError as e:
        print(f"❌ TTS library import failed: {e}")
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    if cuda_available:
        print("✅ System is ready for GPU-accelerated TTS")
        print(f"   Expected speedup: 3-5x compared to CPU")
    else:
        print("ℹ️  System will use CPU for TTS")
        print("   For GPU acceleration, ensure:")
        print("   - NVIDIA GPU is present")
        print("   - Docker started with --gpus all flag")
        print("   - GPU image was built with BUILD_FOR_GPU=1")
    
    print("="*60 + "\n")
    
    return cuda_available

if __name__ == '__main__':
    gpu_available = check_gpu()
    sys.exit(0 if gpu_available else 1)
