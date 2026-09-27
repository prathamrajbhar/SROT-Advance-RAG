export interface ModelOption {
  id: string;
  name: string;
  badge?: string;
  contextWindow?: string;
  description?: string;
}

export const CLOUD_REASONING_MODELS: Record<string, ModelOption[]> = {
  gemini: [
    { id: "gemini-2.0-flash", name: "Gemini 2.0 Flash", badge: "Recommended", contextWindow: "1M", description: "Ultra-fast multimodal reasoning" },
    { id: "gemini-2.5-pro", name: "Gemini 2.5 Pro", badge: "Deep Logic", contextWindow: "2M", description: "Advanced complex problem solving" },
    { id: "gemini-1.5-pro", name: "Gemini 1.5 Pro", badge: "Long Context", contextWindow: "2M", description: "High-capacity document analysis" },
    { id: "gemini-1.5-flash", name: "Gemini 1.5 Flash", badge: "Lightweight", contextWindow: "1M", description: "High-throughput cost efficiency" },
  ],
  openai: [
    { id: "gpt-4o", name: "GPT-4o (Omni)", badge: "Flagship", contextWindow: "128K", description: "High-speed multimodal intelligence" },
    { id: "gpt-4o-mini", name: "GPT-4o Mini", badge: "Fast & Cheap", contextWindow: "128K", description: "Efficient lightweight reasoning" },
    { id: "o3-mini", name: "o3-mini", badge: "STEM Reasoning", contextWindow: "200K", description: "Specialized in code, math, and logic" },
    { id: "gpt-4.5-preview", name: "GPT-4.5 Preview", badge: "Frontier", contextWindow: "128K", description: "Deepest knowledge and reasoning" },
  ],
  anthropic: [
    { id: "claude-3-7-sonnet", name: "Claude 3.7 Sonnet", badge: "Hybrid Reasoning", contextWindow: "200K", description: "Frontier coding & analytical thinking" },
    { id: "claude-3-5-sonnet", name: "Claude 3.5 Sonnet", badge: "Industry Standard", contextWindow: "200K", description: "Exceptional precision & nuanced prose" },
    { id: "claude-3-5-haiku", name: "Claude 3.5 Haiku", badge: "Near-Instant", contextWindow: "200K", description: "Blazing fast sub-second latency" },
  ],
  groq: [
    { id: "llama-3.3-70b-versatile", name: "Llama 3.3 70B", badge: "Fastest LPU", contextWindow: "128K", description: "Sub-150ms 70B parameter open weights" },
    { id: "deepseek-r1-distill-llama-70b", name: "DeepSeek R1 (Distill 70B)", badge: "Reasoning LPU", contextWindow: "128K", description: "Ultra-fast chain-of-thought on Groq" },
    { id: "mixtral-8x7b-32768", name: "Mixtral 8x7B", badge: "MoE", contextWindow: "32K", description: "High-speed sparse Mixture-of-Experts" },
  ],
};

export const CLOUD_EMBEDDING_MODELS: Record<string, ModelOption[]> = {
  gemini: [
    { id: "text-embedding-004", name: "Text Embedding 004", badge: "768 dims", description: "Google's premier multimodal embedding model" },
  ],
  openai: [
    { id: "text-embedding-3-large", name: "Text Embedding 3 Large", badge: "3072 dims", description: "Best overall MTEB benchmark performance" },
    { id: "text-embedding-3-small", name: "Text Embedding 3 Small", badge: "1536 dims", description: "High-speed cost-effective embeddings" },
  ],
  anthropic: [
    { id: "text-embedding-3-large", name: "OpenAI Text Embedding 3 Large", badge: "3072 dims", description: "Cross-provider pairing standard" },
    { id: "voyage-3-large", name: "Voyage AI 3 Large", badge: "1024 dims", description: "Anthropic's recommended partner embedding" },
  ],
  groq: [
    { id: "text-embedding-3-large", name: "OpenAI Text Embedding 3 Large", badge: "3072 dims", description: "Recommended cloud embedding for Groq" },
    { id: "bge-large-en-v1.5", name: "BGE Large EN v1.5", badge: "1024 dims", description: "Open source embedding benchmark leader" },
  ],
};

export const LOCAL_REASONING_MODELS: ModelOption[] = [
  { id: "llama3.3:70b", name: "Llama 3.3 (70B)", badge: "Flagship", description: "Enterprise tier open weights for on-prem servers" },
  { id: "llama3.1:8b", name: "Llama 3.1 (8B)", badge: "Workhorse", description: "Runs comfortably on single workstation GPU" },
  { id: "qwen2.5:72b", name: "Qwen 2.5 (72B)", badge: "Code & Math", description: "Superb multilingual and structured data performance" },
  { id: "deepseek-r1:8b", name: "DeepSeek R1 (8B)", badge: "Reasoning", description: "Local chain-of-thought reasoning distilled model" },
  { id: "deepseek-r1:14b", name: "DeepSeek R1 (14B)", badge: "High Reasoning", description: "Balanced local reasoning for enterprise RAG" },
  { id: "mistral:7b", name: "Mistral (7B)", badge: "Low VRAM", description: "Fast execution with minimal resource footprint" },
  { id: "phi-4:14b", name: "Phi-4 (14B)", badge: "Synthetic Reasoning", description: "Microsoft's high-efficiency small language model" },
];

export const LOCAL_EMBEDDING_MODELS: ModelOption[] = [
  { id: "nomic-embed-text", name: "Nomic Embed Text", badge: "Recommended (8K)", description: "Best general English RAG with 8192-token context" },
  { id: "qwen3-embedding", name: "Qwen 3 Embedding", badge: "Multilingual (32K)", description: "Supports 100+ languages with 32K context window" },
  { id: "bge-m3", name: "BAAI BGE-M3", badge: "Multi-Functionality", description: "Hybrid dense, sparse, and multi-vector retrieval" },
  { id: "all-minilm", name: "All-MiniLM-L6-v2", badge: "Ultra Fast", description: "Minimal CPU/VRAM footprint for rapid local testing" },
];
