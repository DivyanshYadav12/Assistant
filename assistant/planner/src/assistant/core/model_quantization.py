"""Model quantization support for Aether.

Provides utilities for using quantized models to reduce memory usage.
"""

import os
from pathlib import Path
from typing import Optional, List
import subprocess


class ModelQuantization:
    """Handles model quantization and selection."""
    
    # Recommended quantized models
    QUANTIZED_MODELS = {
        "llama3:8b": {
            "quantized": "llama3:8b-q4_K_M",
            "original_size_gb": 4.7,
            "quantized_size_gb": 2.2,
            "memory_reduction": 0.53,
            "performance": "Good for most tasks"
        },
        "llama3:8b-instruct": {
            "quantized": "llama3:8b-instruct-q4_K_M",
            "original_size_gb": 4.7,
            "quantized_size_gb": 2.2,
            "memory_reduction": 0.53,
            "performance": "Good for most tasks"
        },
        "qwen2.5:1.5b-instruct": {
            "quantized": "qwen2.5:1.5b-instruct-q4_K_M",
            "original_size_gb": 0.9,
            "quantized_size_gb": 0.5,
            "memory_reduction": 0.44,
            "performance": "Minimal impact"
        }
    }
    
    def __init__(self):
        self.ollama_url = os.environ.get("AETHER_OLLAMA_URL", "http://127.0.0.1:11434")
    
    def get_recommended_model(self, base_model: str) -> Optional[str]:
        """Get the recommended quantized version of a model.
        
        Args:
            base_model: The base model name (e.g., "llama3:8b")
            
        Returns:
            The quantized model name, or None if not available
        """
        return self.QUANTIZED_MODELS.get(base_model, {}).get("quantized")
    
    def get_size_savings(self, base_model: str) -> Optional[dict]:
        """Get size savings information for a model.
        
        Args:
            base_model: The base model name
            
        Returns:
            Dictionary with size information, or None if not available
        """
        return self.QUANTIZED_MODELS.get(base_model)
    
    def list_available_models(self) -> List[str]:
        """List all available Ollama models.
        
        Returns:
            List of model names
        """
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    # Skip header line
                    models = []
                    for line in lines[1:]:
                        parts = line.split()
                        if parts:
                            models.append(parts[0])
                    return models
        except Exception as e:
            print(f"Failed to list models: {e}")
        
        return []
    
    def download_quantized_model(self, base_model: str) -> bool:
        """Download the quantized version of a model.
        
        Args:
            base_model: The base model name
            
        Returns:
            True if successful, False otherwise
        """
        quantized = self.get_recommended_model(base_model)
        if not quantized:
            print(f"No quantized version available for {base_model}")
            return False
        
        print(f"Downloading quantized model: {quantized}")
        print(f"This will save ~{self.get_size_savings(base_model)['original_size_gb'] - self.get_size_savings(base_model)['quantized_size_gb']:.1f} GB")
        
        try:
            result = subprocess.run(
                ["ollama", "pull", quantized],
                timeout=600
            )
            return result.returncode == 0
        except Exception as e:
            print(f"Failed to download quantized model: {e}")
            return False
    
    def check_model_exists(self, model_name: str) -> bool:
        """Check if a model exists locally.
        
        Args:
            model_name: The model name
            
        Returns:
            True if model exists, False otherwise
        """
        models = self.list_available_models()
        return model_name in models
    
    def get_optimal_model_config(self, ram_gb: int) -> dict:
        """Get optimal model configuration based on available RAM.
        
        Args:
            ram_gb: Available RAM in GB
            
        Returns:
            Dictionary with recommended model configuration
        """
        if ram_gb >= 16:
            # Can use full 8B model
            return {
                "smart_model": "llama3:8b",
                "fast_model": "qwen2.5:1.5b-instruct",
                "use_quantized": False,
                "reason": "Sufficient RAM for full models"
            }
        elif ram_gb >= 8:
            # Use quantized 8B model
            return {
                "smart_model": "llama3:8b-q4_K_M",
                "fast_model": "qwen2.5:1.5b-instruct-q4_K_M",
                "use_quantized": True,
                "reason": "Using quantized models for memory efficiency"
            }
        else:
            # Use only fast model
            return {
                "smart_model": "qwen2.5:1.5b-instruct",
                "fast_model": "qwen2.5:1.5b-instruct",
                "use_quantized": True,
                "reason": "Insufficient RAM for 8B model"
            }


def print_quantization_guide():
    """Print a guide about model quantization."""
    print("=" * 60)
    print("Aether Model Quantization Guide")
    print("=" * 60)
    print()
    print("What is Model Quantization?")
    print("-" * 60)
    print("Quantization reduces model precision from 16-bit to 4-bit,")
    print("significantly reducing memory usage with minimal performance loss.")
    print()
    print("Benefits:")
    print("  • Reduces model size by ~50%")
    print("  • Lowers RAM requirements")
    print("  • Faster loading times")
    print("  • Minimal quality loss for most tasks")
    print()
    print("Recommended Quantized Models:")
    print("-" * 60)
    for base, info in ModelQuantization.QUANTIZED_MODELS.items():
        print(f"\n{base}:")
        print(f"  Quantized: {info['quantized']}")
        print(f"  Size: {info['original_size_gb']} GB → {info['quantized_size_gb']} GB")
        print(f"  Memory reduction: {info['memory_reduction']*100:.0f}%")
        print(f"  Performance: {info['performance']}")
    print()
    print("How to Use:")
    print("-" * 60)
    print("1. Download quantized model:")
    print("   ollama pull llama3:8b-q4_K_M")
    print()
    print("2. Update .env file:")
    print("   AETHER_LLM_MODEL=llama3:8b-q4_K_M")
    print()
    print("3. Restart Aether")
    print()
    print("RAM Requirements:")
    print("-" * 60)
    print("  16GB+ RAM: Use full models (best quality)")
    print("   8GB RAM: Use quantized models (good quality)")
    print("   <8GB RAM: Use 1.5B model only (basic)")
    print()
    print("=" * 60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "guide":
        print_quantization_guide()
    else:
        # Check available models
        quant = ModelQuantization()
        models = quant.list_available_models()
        print("Available models:")
        for model in models:
            print(f"  - {model}")
        
        print("\nQuantization recommendations:")
        for base in quant.QUANTIZED_MODELS.keys():
            if base in models:
                quantized = quant.get_recommended_model(base)
                savings = quant.get_size_savings(base)
                print(f"\n{base}:")
                print(f"  Quantized: {quantized}")
                print(f"  Savings: {savings['original_size_gb'] - savings['quantized_size_gb']:.1f} GB")
