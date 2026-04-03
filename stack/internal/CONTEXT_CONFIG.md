# Context Window Configuration

Stack 2.9 uses full 128K context window (131072 tokens) to provide complete repository awareness.

## Settings
- max_model_len: 131072
- max_seq_length: 131072
- block_size: 16 or 32 (adjust for memory/performance tradeoff)

## Memory Requirements
| Context | A100 80GB (4-bit) | H100 80GB (4-bit) |
|---------|-------------------|-------------------|
| 32K     | ~20GB             | ~18GB             |
| 64K     | ~35GB             | ~32GB             |
| 128K    | ~60GB             | ~55GB             |

Throughput decreases slightly at longer contexts (~30% slower at 128K vs 32K) but provides full repository context.

