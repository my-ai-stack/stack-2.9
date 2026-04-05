#!/usr/bin/env python3
"""
Synthetic Code Completion Training Data Generator for Stack 2.9
Generates training examples for pure code completion without tools.
"""

import json
import random
import argparse
from pathlib import Path
from typing import Dict, List

LANGUAGES = ["python", "javascript", "go", "rust", "typescript"]
DIFFICULTY_EASY = "easy"
DIFFICULTY_MEDIUM = "medium"
DIFFICULTY_HARD = "hard"

# Code templates organized by language -> difficulty -> templates
CODE_TEMPLATES = {
    "python": {
        DIFFICULTY_EASY: [
            {"context": "def greet(name):", "completion": '    return f"Hello, {name}!"', "description": "Simple greeting function"},
            {"context": "numbers = [1, 2, 3, 4, 5]\n\n", "completion": "for num in numbers:\n    print(num)", "description": "Loop through list"},
            {"context": "class Person:\n    def __init__(self, name):", "completion": "        self.name = name", "description": "Class init"},
            {"context": "def add(a, b):\n    ", "completion": "    return a + b", "description": "Add function"},
            {"context": "if x > 0:\n    print('positive')\nelif x < 0:\n    ", "completion": "    print('negative')", "description": "Conditional"},
        ],
        DIFFICULTY_MEDIUM: [
            {"context": "def fibonacci(n):\n    if n <= 1:\n        return n\n    ", "completion": "    return fibonacci(n-1) + fibonacci(n-2)", "description": "Fibonacci"},
            {"context": "class Calculator:\n    def __init__(self):\n        self.result = 0\n    \n    def add(self, x):\n        ", "completion": "        self.result += x\n        return self.result", "description": "Calculator"},
            {"context": "async def fetch_data(url):\n    async with aiohttp.ClientSession() as session:\n        async with session.get(url) as response:\n            ", "completion": "            return await response.json()", "description": "Async HTTP"},
            {"context": "def validate_email(email):\n    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'\n    ", "completion": "    return re.match(pattern, email) is not None", "description": "Email validation"},
            {"context": "@app.route('/users/<int:user_id>')\ndef get_user(user_id):\n    user = User.query.get_or_404(user_id)\n    ", "completion": "    return jsonify(user.to_dict())", "description": "Flask route"},
        ],
        DIFFICULTY_HARD: [
            {"context": "class LRUCache:\n    def __init__(self, capacity):\n        self.capacity = capacity\n        self.cache = OrderedDict()\n    \n    def get(self, key):\n        if key not in self.cache:\n            return -1\n        ", "completion": "        self.cache.move_to_end(key)\n        return self.cache[key]", "description": "LRU Cache"},
            {"context": "def merge_sort(arr):\n    if len(arr) <= 1:\n        return arr\n    \n    mid = len(arr) // 2\n    left = merge_sort(arr[:mid])\n    right = merge_sort(arr[mid:])\n    ", "completion": "    return merge(left, right)", "description": "Merge sort"},
            {"context": "class BinaryTree:\n    def __init__(self, value):\n        self.value = value\n        self.left = None\n        self.right = None\n    \n    def inorder(self, node, result=None):\n        if result is None:\n            result = []\n        if node:\n            ", "completion": "            self.inorder(node.left, result)\n            result.append(node.value)\n            self.inorder(node.right, result)\n        return result", "description": "Binary tree inorder"},
            {"context": "def bellman_ford(graph, source):\n    dist = {v: float('inf') for v in graph}\n    dist[source] = 0\n    \n    for _ in range(len(graph) - 1):\n        for u, v, w in graph.edges:\n            if dist[u] != float('inf') and dist[u] + w < dist[v]:\n                ", "completion": "                dist[v] = dist[u] + w\n    return dist", "description": "Bellman-Ford"},
        ],
    },
    "javascript": {
        DIFFICULTY_EASY: [
            {"context": "const greet = (name) => {", "completion": '    return `Hello, ${name}!`;', "description": "Arrow greeting"},
            {"context": "const numbers = [1, 2, 3, 4, 5];\n\n", "completion": "numbers.forEach(num => console.log(num));", "description": "forEach loop"},
            {"context": "class Person {\n  constructor(name) {", "completion": "    this.name = name;", "description": "JS class constructor"},
            {"context": "const add = (a, b) => {", "completion": "  return a + b;", "description": "Add function"},
            {"context": "if (x > 0) {\n  console.log('positive');\n} else if (x < 0) {\n  ", "completion": "  console.log('negative');", "description": "Conditional"},
        ],
        DIFFICULTY_MEDIUM: [
            {"context": "const fetchData = async (url) => {\n  try {\n    const response = await fetch(url);\n    ", "completion": "    return await response.json();\n  } catch (error) {\n    console.error('Error:', error);\n  }", "description": "Async fetch"},
            {"context": "class EventEmitter {\n  constructor() {\n    this.events = {};\n  }\n  \n  on(event, callback) {\n    ", "completion": "    if (!this.events[event]) this.events[event] = [];\n    this.events[event].push(callback);", "description": "Event emitter"},
            {"context": "const debounce = (func, delay) => {\n  let timeoutId;\n  return (...args) => {\n    clearTimeout(timeoutId);\n    ", "completion": "    timeoutId = setTimeout(() => func.apply(this, args), delay);", "description": "Debounce"},
            {"context": "const memoize = (fn) => {\n  const cache = new Map();\n  return (n) => {\n    if (cache.has(n)) {\n      return cache.get(n);\n    }\n    ", "completion": "    const result = fn(n);\n    cache.set(n, result);\n    return result;", "description": "Memoize"},
        ],
        DIFFICULTY_HARD: [
            {"context": "class PromisePool {\n  constructor(maxConcurrent) {\n    this.maxConcurrent = maxConcurrent;\n    this.running = 0;\n    this.queue = [];\n  }\n  \n  add(promiseFn) {\n    return new Promise((resolve, reject) => {\n      ", "completion": "      this.queue.push({ promiseFn, resolve, reject });\n      this.process();\n    });", "description": "Promise pool"},
            {"context": "const virtualDOM = {\n  createElement(tag, props, ...children) {\n    return {\n      tag,\n      props: props || {},\n      children: children.flat(),\n    };\n  },\n  render(vnode, container) {\n    ", "completion": "    const el = document.createElement(vnode.tag);\n    Object.entries(vnode.props || {}).forEach(([key, value]) => el.setAttribute(key, value));\n    vnode.children.forEach(child => {\n      if (typeof child === 'string') el.appendChild(document.createTextNode(child));\n      else this.render(child, el);\n    });\n    container.appendChild(el);", "description": "Virtual DOM"},
        ],
    },
    "go": {
        DIFFICULTY_EASY: [
            {"context": "func greet(name string) string {", "completion": '    return "Hello, " + name + "!"', "description": "Greet function"},
            {"context": "func add(a, b int) int {", "completion": "    return a + b", "description": "Add function"},
            {"context": "type Person struct {\n    Name string\n    ", "completion": "    Age  int", "description": "Struct definition"},
            {"context": "for i := 0; i < 10; i++ {\n    ", "completion": "    fmt.Println(i)", "description": "For loop"},
            {"context": "if x > 0 {\n    fmt.Println(\"positive\")\n} else {\n    ", "completion": '    fmt.Println("non-positive")', "description": "If-else"},
        ],
        DIFFICULTY_MEDIUM: [
            {"context": "func (p Person) Greet() string {", "completion": '    return fmt.Sprintf("Hello, %s!", p.Name)', "description": "Method"},
            {"context": "func worker(jobs <-chan int, results chan<- int) {\n    for j := range jobs {\n        ", "completion": "        results <- j * 2", "description": "Worker goroutine"},
            {"context": "type Handler interface {\n    Handle(ctx context.Context, req Request) Response\n    ", "completion": "    Cleanup(ctx context.Context)", "description": "Interface"},
            {"context": "func fetchData(url string) ([]byte, error) {\n    resp, err := http.Get(url)\n    if err != nil {\n        return nil, err\n    }\n    defer resp.Body.Close()\n    ", "completion": "    return io.ReadAll(resp.Body)", "description": "HTTP GET"},
        ],
        DIFFICULTY_HARD: [
            {"context": "type TreeNode struct {\n    Val   int\n    Left  *TreeNode\n    Right *TreeNode\n}\n\nfunc (root *TreeNode) InorderTraversal() []int {\n    var result []int\n    var inorder func(*TreeNode)\n    inorder = func(node *TreeNode) {\n        if node == nil {\n            return\n        }\n        ", "completion": "        inorder(node.Left)\n        result = append(result, node.Val)\n        inorder(node.Right)", "description": "Tree inorder"},
            {"context": "func (c *Client) StreamProcess(ctx context.Context, req *Request, stream chan<- *Response) error {\n    for {\n        select {\n        case <-ctx.Done():\n            return ctx.Err()\n        default:\n            result, err := c.processOne(req)\n            if err != nil {\n                return err\n            }\n            ", "completion": "            select {\n            case stream <- result:\n            case <-ctx.Done():\n                return ctx.Err()\n            }", "description": "Streaming"},
        ],
    },
    "rust": {
        DIFFICULTY_EASY: [
            {"context": "fn greet(name: &str) -> String {", "completion": '    format!("Hello, {}!", name)', "description": "Greet function"},
            {"context": "fn add(a: i32, b: i32) -> i32 {", "completion": "    a + b", "description": "Add function"},
            {"context": "struct Person {\n    name: String,\n    ", "completion": "    age: u32,", "description": "Struct"},
            {"context": "let numbers = vec![1, 2, 3, 4, 5];\nfor num in &numbers {\n    ", "completion": "    println!(\"{}\", num);", "description": "For loop"},
            {"context": "fn main() {\n    let result = match value {\n        Some(x) => x,\n        ", "completion": "        None => 0,", "description": "Match"},
        ],
        DIFFICULTY_MEDIUM: [
            {"context": "impl Person {\n    fn new(name: String, age: u32) -> Self {", "completion": "        Person { name, age }", "description": "Constructor"},
            {"context": "fn fetch_data(url: &str) -> Result<String, Error> {\n    let response = reqwest::blocking::get(url)?;\n    ", "completion": "    let body = response.text()?;\n    Ok(body)", "description": "HTTP request"},
            {"context": "fn process_items<T: Display>(items: Vec<T>) -> String {\n    items\n        .iter()\n        .enumerate()\n        .map(|(i, item)| format!(\"{}: {}\", i, item))\n        ", "completion": "        .collect::<Vec<_>>()\n        .join(\", \")", "description": "Iterator chain"},
            {"context": "fn spawn_worker(jobs: Arc<Mutex<Vec<Job>>>) {\n    thread::spawn(move || {\n        loop {\n            let job = {\n                let mut jobs = jobs.lock().unwrap();\n                jobs.pop()\n            };\n            match job {\n                Some(job) => job.execute(),\n                ", "completion": "                None => break,\n            };\n        }\n    });", "description": "Worker thread"},
        ],
        DIFFICULTY_HARD: [
            {"context": "pub struct LRUCache<K, V> {\n    capacity: usize,\n    cache: LinkedHashMap<K, V>,\n}\n\nimpl<K: Eq + Hash + Clone, V: Clone> LRUCache<K, V> {\n    pub fn get(&mut self, key: &K) -> Option<&V> {\n        if self.cache.contains_key(key) {\n            ", "completion": "            self.cache.remove(key);\n            let value = self.cache[key].clone();\n            self.cache.insert(key.clone(), value);\n            self.cache.get(key)\n        } else {\n            None\n        }", "description": "LRU Cache"},
            {"context": "pub trait Observer<T> {\n    fn update(&self, event: &T);\n}\n\npub struct Subject<T> {\n    observers: Vec<Box<dyn Observer<T>>>,\n}\n\nimpl<T> Subject<T> {\n    pub fn notify(&self, event: &T) {\n        for observer in &self.observers {\n            ", "completion": "            observer.update(event);", "description": "Observer pattern"},
        ],
    },
}

VARIANTS = ["basic", "explain", "debug", "optimize"]

VARIANT_PROMPTS = {
    "basic": {"system": "You are a helpful AI assistant that helps with code completion.", "user_prefix": "Complete the following code:\n\n"},
    "explain": {"system": "You are a helpful AI assistant that explains and completes code.", "user_prefix": "Explain what this code does and complete it:\n\n"},
    "debug": {"system": "You are a helpful AI assistant that finds bugs and suggests fixes.", "user_prefix": "There's a bug in this code. Fix and complete it:\n\n"},
    "optimize": {"system": "You are a helpful AI assistant that optimizes code for performance.", "user_prefix": "Optimize this code and complete it:\n\n"},
}


def create_completion_example(context, completion, language, difficulty, variant, description):
    """Create a single code completion example."""
    variant_info = VARIANT_PROMPTS[variant]
    messages = [
        {"role": "system", "content": variant_info["system"]},
        {"role": "user", "content": f"{variant_info['user_prefix']}```{language}\n{context}```"},
        {"role": "assistant", "content": f"Here's the completed code:\n\n```{language}\n{context}{completion}\n```"}
    ]
    return {
        "messages": messages,
        "language": language,
        "difficulty": difficulty,
        "variant": variant,
        "description": description,
        "context": context,
        "completion": completion,
    }


def generate_examples_for_language(language, difficulty, num_examples, variants):
    """Generate examples for a specific language and difficulty."""
    templates = CODE_TEMPLATES[language][difficulty]
    examples = []
    for i in range(num_examples):
        template = templates[i % len(templates)]
        variant = random.choice(variants)
        example = create_completion_example(
            context=template["context"],
            completion=template["completion"],
            language=language,
            difficulty=difficulty,
            variant=variant,
            description=template["description"]
        )
        examples.append(example)
    return examples


def generate_dataset(num_examples=1000, languages=None, difficulties=None, variants=None, balance=True):
    """Generate the complete dataset."""
    if languages is None:
        languages = LANGUAGES
    if difficulties is None:
        difficulties = [DIFFICULTY_EASY, DIFFICULTY_MEDIUM, DIFFICULTY_HARD]
    if variants is None:
        variants = VARIANTS
    
    examples = []
    
    if balance:
        examples_per_lang = num_examples // len(languages)
        examples_per_diff = examples_per_lang // len(difficulties)
        remainder = num_examples % (len(languages) * len(difficulties))
        
        for lang in languages:
            for diff_idx, diff in enumerate(difficulties):
                count = examples_per_diff + (1 if diff_idx < remainder else 0)
                lang_examples = generate_examples_for_language(lang, diff, count, variants)
                examples.extend(lang_examples)
    else:
        for _ in range(num_examples):
            lang = random.choice(languages)
            diff = random.choice(difficulties)
            template = random.choice(CODE_TEMPLATES[lang][diff])
            variant = random.choice(variants)
            example = create_completion_example(
                context=template["context"],
                completion=template["completion"],
                language=lang,
                difficulty=diff,
                variant=variant,
                description=template["description"]
            )
            examples.append(example)
    
    random.shuffle(examples)
    return examples


def save_jsonl(examples, output_path):
    """Save examples to JSONL format."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        for example in examples:
            f.write(json.dumps(example, ensure_ascii=False) + '\n')


def save_json(examples, output_path):
    """Save examples to JSON format."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(examples, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic code completion training data")
    parser.add_argument("--num-examples", type=int, default=1000, help="Number of examples to generate")
    parser.add_argument("--output-dir", type=str, default="training-data/code-completion", help="Output directory")
    parser.add_argument("--output-format", choices=["jsonl", "json", "both"], default="jsonl", help="Output format")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    random.seed(args.seed)
    
    print(f"Generating {args.num_examples} code completion training examples...")
    print(f"   Languages: {LANGUAGES}")
    print(f"   Output directory: {args.output_dir}")
    
    examples = generate_dataset(
        num_examples=args.num_examples,
        languages=LANGUAGES,
        difficulties=[DIFFICULTY_EASY, DIFFICULTY_MEDIUM, DIFFICULTY_HARD],
        variants=VARIANTS
    )
    
    output_dir = Path(args.output_dir)
    
    if args.output_format in ["jsonl", "both"]:
        jsonl_path = output_dir / "code_completion.jsonl"
        save_jsonl(examples, str(jsonl_path))
        print(f"Saved JSONL: {jsonl_path}")
    
    if args.output_format in ["json", "both"]:
        json_path = output_dir / "code_completion.json"
        save_json(examples, str(json_path))
        print(f"Saved JSON: {json_path}")
    
    # Statistics
    print(f"\nStatistics:")
    print(f"   Total examples: {len(examples)}")
    
    lang_counts = {}
    diff_counts = {}
    for ex in examples:
        lang_counts[ex["language"]] = lang_counts.get(ex["language"], 0) + 1
        diff_counts[ex["difficulty"]] = diff_counts.get(ex["difficulty"], 0) + 1
    
    print(f"   By language:")
    for lang, count in sorted(lang_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"     - {lang}: {count}")
    
    print(f"   By difficulty:")
    for diff, count in sorted(diff_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"     - {diff}: {count}")
    
    print(f"\nGeneration complete!")


if __name__ == "__main__":
    main()
