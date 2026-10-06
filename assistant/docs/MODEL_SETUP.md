# Aether Model Setup Guide

## Overview

Aether uses an adaptive multi-model architecture for optimal performance:

- **Tier 1 (Fast)**: qwen2.5:1.5b-instruct - Simple commands, routing
- **Tier 2 (Smart)**: llama3.1:8b-instruct - Conversation, coding, knowledge
- **Tier 3 (Cloud)**: OpenAI GPT-4o / Claude 3.5 - Complex reasoning (optional)

## Prerequisites

### Hardware Requirements
- **RAM**: 16GB+ (for 8B model)
- **Storage**: 20GB+ free space
- **Ollama**: Installed and running

### Software Requirements
```powershell
# Install Ollama if not already installed
# Download from: https://ollama.com/download
# Or use winget:
winget install Ollama.Ollama
```

## Step 1: Download Models

### Start Ollama
```powershell
ollama serve
```

### Download Fast Model (Tier 1)
```powershell
ollama pull qwen2.5:1.5b-instruct
```
- Size: ~1GB
- RAM: ~2GB
- Speed: Very fast (< 1s)
- Use: Simple commands, routing

### Download Smart Model (Tier 2) - RECOMMENDED
```powershell
ollama pull llama3:8b
```
- Size: ~4.7GB
- RAM: ~8GB
- Speed: Moderate (2-5s)
- Use: Conversation, coding, knowledge
- **Best for your 16GB RAM**

### Optional: Download Cloud Dependencies
```powershell
cd d:\hive\assistant\planner
.\.venv\Scripts\pip install openai anthropic
```

## Step 2: Configure Environment Variables

### Option A: Set in PowerShell (Session Only)
```powershell
# Smart model for conversations
$env:AETHER_SMART_MODEL="llama3.1:8b-instruct"

# Optional: Cloud API for complex tasks
$env:AETHER_CLOUD_API_KEY="your-api-key-here"
$env:AETHER_CLOUD_PROVIDER="openai"  # or "anthropic"
```

### Option B: Set in .env File (Persistent)
Create `d:\hive\assistant\planner\.env`:
```env
AETHER_SMART_MODEL=llama3.1:8b-instruct
AETHER_CLOUD_API_KEY=your-api-key-here
AETHER_CLOUD_PROVIDER=openai
```

## Step 3: Verify Installation

### Test Models
```powershell
# Test fast model
ollama run qwen2.5:1.5b-instruct "What is 2+2?"

# Test smart model
ollama run llama3:8b "What is neural network?"
```

### Test with Aether
```powershell
# Start planner
cd d:\hive\assistant\planner
.\.venv\Scripts\python.exe -m assistant.core.listener

# Start wake word listener
cd d:\hive\assistant\planner
.\.venv\Scripts\python.exe -m assistant.core.wake

# Try conversation
Say: "Computer"
Then: "What is artificial intelligence?"
```

## Model Comparison

| Model | Size | RAM | Speed | Quality | Best For |
|-------|------|-----|-------|---------|----------|
| qwen2.5:1.5b | 1GB | 2GB | <1s | Basic | Simple commands |
| llama3.1:8b | 4.7GB | 8GB | 2-5s | Good | Conversation, coding |
| GPT-4o (cloud) | N/A | N/A | 5-10s | Excellent | Complex reasoning |

## Troubleshooting

### Out of Memory Error
**Problem**: "CUDA out of memory" or system slowdown
**Solution**: Use the 1.5B model instead
```powershell
$env:AETHER_SMART_MODEL="qwen2.5:1.5b-instruct"
```

### Model Not Found
**Problem**: "model not found" error
**Solution**: Download the model
```powershell
ollama pull llama3.1:8b-instruct
```

### Slow Responses
**Problem**: Responses take 10+ seconds
**Solution**: 
1. Check available RAM (Task Manager)
2. Use smaller model
3. Close other applications

## Performance Tips

### Optimize for Speed
```powershell
# Use fast model for everything
$env:AETHER_SMART_MODEL="qwen2.5:1.5b-instruct"
```

### Optimize for Quality
```powershell
# Use smart model for everything
$env:AETHER_SMART_MODEL="llama3.1:8b-instruct"
```

### Adaptive (Recommended)
```powershell
# Let Aether choose automatically
# Fast model for simple tasks
# Smart model for conversations
# Cloud for complex tasks (with approval)
```

## Advanced: Fine-Tuning (Optional)

If you want to fine-tune a model for your specific use case:

1. **Collect Data**: Save your conversation logs
2. **Prepare Dataset**: Format for training
3. **Use Axolotl**: Training framework
4. **Deploy**: Replace default model

This is advanced and requires GPU. Not recommended for beginners.

## Next Steps

After setting up models:

1. Test conversation quality
2. Adjust complexity thresholds if needed
3. Configure cloud API for complex tasks (optional)
4. Fine-tune personality in `llm.py` system prompt
