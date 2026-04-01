// Stack 2.9 - App JavaScript

document.addEventListener('DOMContentLoaded', () => {
    initMobileMenu();
    initCodeDemo();
    initDemoTerminal();
    initSmoothScroll();
    initAnimations();
});

// Mobile Menu Toggle
function initMobileMenu() {
    const toggle = document.getElementById('mobileToggle');
    const navLinks = document.getElementById('navLinks');
    
    if (toggle && navLinks) {
        toggle.addEventListener('click', () => {
            navLinks.classList.toggle('active');
            toggle.classList.toggle('active');
        });
        
        // Close on link click
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('active');
                toggle.classList.remove('active');
            });
        });
    }
}

// Animated Code Editor Demo
function initCodeDemo() {
    const codeLines = document.getElementById('codeLines');
    if (!codeLines) return;
    
    const codeSnippets = [
        { text: 'import stack_2_9', type: 'keyword' },
        { text: 'from stack_2_9 import Agent', type: 'keyword' },
        { text: '', type: '' },
        { text: '# Initialize your AI companion', type: 'comment' },
        { text: 'agent = stack_2_9.Agent(', type: 'function' },
        { text: '    name="dev_assistant",', type: '' },
        { text: '    self_evolving=True,', type: 'variable' },
        { text: '    memory_persistent=True', type: 'variable' },
        { text: ')', type: '' },
        { text: '', type: '' },
        { text: '# It learns from you!', type: 'comment' },
        { text: 'response = agent.chat("Build a web app")', type: 'function' },
        { text: 'print(response)  # Getting smarter...', type: 'string' },
    ];
    
    let lineIndex = 0;
    const typeSpeed = 30;
    const lineDelay = 200;
    
    function typeLine() {
        if (lineIndex >= codeSnippets.length) {
            lineIndex = 0;
            codeLines.innerHTML = '';
            setTimeout(typeLine, 2000);
            return;
        }
        
        const snippet = codeSnippets[lineIndex];
        const lineDiv = document.createElement('div');
        lineDiv.className = 'code-line';
        
        const numberSpan = document.createElement('span');
        numberSpan.className = 'line-number';
        numberSpan.textContent = lineIndex + 1;
        
        const contentSpan = document.createElement('span');
        contentSpan.className = `line-content ${snippet.type}`;
        
        lineDiv.appendChild(numberSpan);
        lineDiv.appendChild(contentSpan);
        codeLines.appendChild(lineDiv);
        
        let charIndex = 0;
        const text = snippet.text;
        
        function typeChar() {
            if (charIndex < text.length) {
                contentSpan.textContent += text[charIndex];
                charIndex++;
                setTimeout(typeChar, typeSpeed);
            } else {
                lineIndex++;
                setTimeout(typeLine, lineDelay);
            }
        }
        
        typeChar();
    }
    
    typeLine();
}

// Demo Terminal Interactivity
function initDemoTerminal() {
    const input = document.getElementById('demoInput');
    const output = document.getElementById('demoOutput');
    const clearBtn = document.getElementById('clearDemo');
    
    if (!input || !output) return;
    
    const responses = {
        help: `📚 Available commands:
  • explain self-evolution - How it learns
  • list tools              - See all 37 tools
  • benchmark              - Performance stats
  • features               - What makes it unique
  • memory                 - How it remembers`,
        
        'explain self-evolution': `🧠 Self-Evolution Process:
  
1. OBSERVE - Watches problem-solving
2. LEARN - Extracts patterns from successes  
3. REMEMBER - Stores in persistent memory
4. APPLY - Uses knowledge in future tasks
5. EVOLVE - Gradually becomes smarter

The more you use it, the smarter it gets!`,
        
        'list tools': `🔧 Available Tools (37 total):
  
File Operations: read, write, edit, search, move
Code: execute, debug, test, refactor
System: shell, git, docker, process
Data: parse, format, validate, convert
APIs: http, websocket, database queries

All accessible via natural language!`,
        
        benchmark: `📊 Benchmark Results:
  
• HumanEval:    76.8% (Python coding)
• MBPP:         82.3% (Basic programming)
• Tool Use:     94.1% (OpenClaw tools)
• Self-Improvement: Evolves with use

Competitive with top open-source models!`,
        
        features: `✨ Stack 2.9 Features:
  
• Self-Evolving - Learns from every chat
• Codebase-Aware - Understands your project
• 37 Tools - Coding, debugging, deployment
• Persistent Memory - Remembers past talks
• Multi-Agent - Work with multiple AIs
• Self-Hostable - Your data, your control`,
        
        memory: `💾 Memory System:
  
• Conversation memory - Remembers chats
• Pattern learning - Extracts reusable knowledge
• Cross-session persistence - Survives restarts
• Project-specific expertise - Learns your codebase

Unlike other AIs that reset each session!`,
        
        default: `🤖 Stack 2.9 Interactive Demo

Type 'help' for available commands, or ask me anything about Stack 2.9!`
    };
    
    function addOutput(text, type = 'assistant') {
        const line = document.createElement('div');
        line.className = `terminal-line ${type}`;
        line.textContent = text;
        output.appendChild(line);
        output.scrollTop = output.scrollHeight;
    }
    
    function handleCommand(cmd) {
        const trimmed = cmd.trim().toLowerCase();
        addOutput(`> ${cmd}`, 'user');
        
        setTimeout(() => {
            const response = responses[trimmed] || responses.default;
            addOutput(response, 'assistant');
        }, 300);
    }
    
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && input.value.trim()) {
            handleCommand(input.value);
            input.value = '';
        }
    });
    
    // Demo command buttons
    document.querySelectorAll('.demo-cmd').forEach(btn => {
        btn.addEventListener('click', () => {
            input.value = btn.dataset.cmd;
            input.focus();
            handleCommand(btn.dataset.cmd);
            input.value = '';
        });
    });
    
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            output.innerHTML = '<div class="terminal-line system">🤖 Stack 2.9 ready! Type a command...</div>';
        });
    }
}

// Smooth Scroll
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href === '#') return;
            
            e.preventDefault();
            const target = document.querySelector(href);
            
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Scroll Animations
function initAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    // Observe feature cards
    document.querySelectorAll('.feature-card, .benchmark-card, .faq-item, .step').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
    
    // Add animation class
    document.addEventListener('scroll', () => {
        document.querySelectorAll('.animate-in').forEach(el => {
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        });
    }, { passive: true });
    
    // Trigger initial check
    setTimeout(() => {
        document.querySelectorAll('.feature-card, .benchmark-card, .faq-item, .step').forEach(el => {
            const rect = el.getBoundingClientRect();
            if (rect.top < window.innerHeight - 50) {
                el.style.opacity = '1';
                el.style.transform = 'translateY(0)';
            }
        });
    }, 100);
}

// Navbar scroll effect
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        if (window.scrollY > 50) {
            navbar.style.background = 'rgba(10, 10, 15, 0.95)';
        } else {
            navbar.style.background = 'rgba(10, 10, 15, 0.8)';
        }
    }
}, { passive: true });

console.log('🤖 Stack 2.9 Website Initialized');