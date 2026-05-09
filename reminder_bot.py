#!/usr/bin/env python3
"""
DSA SRS Reminder Bot
Sends daily reminders to Telegram with inline buttons to track progress
Uses Claude API (Sonnet) to generate contextual messages
Uses SM-2 spaced repetition algorithm for scheduling
"""

import json
import sys
import argparse
import requests
import logging
import logging.handlers
import time
from datetime import datetime, timedelta
from pathlib import Path
from anthropic import Anthropic

# Global logger and start time
logger = None
mode_start_time = None

# Fix Windows Unicode encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Configuration
SCRIPT_DIR = Path(__file__).parent
TRACKER_FILE = SCRIPT_DIR / "dsa_tracker.json"
BOT_TOKEN = "8758562298:AAGEJncaC-wMF7fXGwQJP3STHwAW9vbO6VI"
CHAT_ID = "5466701469"

# Load environment variables from .env file (needed for Task Scheduler)
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path=SCRIPT_DIR / ".env")

# Get Claude API key from environment or ask user
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")

def setup_logging(mode):
    """Configure logging with daily rotation and custom formatter"""
    global logger, mode_start_time

    mode_start_time = time.time()
    logs_dir = SCRIPT_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)

    logger = logging.getLogger("dsa_bot")
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers
    logger.handlers.clear()

    # Daily rotating file handler (1 file per day, keep 30 days)
    log_file = logs_dir / f"dsa_bot_{datetime.now().strftime('%Y-%m-%d')}.log"
    file_handler = logging.handlers.TimedRotatingFileHandler(
        str(log_file),
        when="midnight",
        interval=1,
        backupCount=30
    )
    file_handler.setLevel(logging.DEBUG)

    # Stream handler for stdout (uses system default encoding)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)

    # Custom formatter: timestamp [LEVEL] [mode] message
    formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d [%(levelname)-5s] [%(mode)-9s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Add a custom filter to inject mode into log records
    class ModeFilter(logging.Filter):
        def __init__(self, mode_name):
            self.mode_name = mode_name
        def filter(self, record):
            record.mode = self.mode_name
            return True

    mode_filter = ModeFilter(mode)
    file_handler.addFilter(mode_filter)
    stream_handler.addFilter(mode_filter)

    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    # Log startup
    logger.info(f"START: {mode}")
    env_keys = [k for k in ["ANTHROPIC_API_KEY", "CLAUDE_API_KEY", "TELEGRAM_BOT_TOKEN"] if os.getenv(k)]
    env_status = "SET" if env_keys else "NOT SET"
    tracker_exists = "FOUND" if TRACKER_FILE.exists() else "MISSING"
    logger.info(f".env loaded: YES | API keys: {env_status} | Tracker file: {tracker_exists}")

class APILogger:
    """Log external API requests and responses to both text and JSON formats"""

    # Service registry: define which services to log
    SERVICE_REGISTRY = {
        "telegram": {"json_file": "telegram_requests_{}.json"},
        "claude": {"json_file": "claude_requests_{}.json"}
    }

    # Sanitization rules per service
    SANITIZATION_RULES = {
        "telegram": {
            "endpoint_mask": r"(bot\d+:[A-Za-z0-9_-]+)",
            "headers_to_mask": [],
            "body_keys_to_mask": []
        },
        "claude": {
            "endpoint_mask": None,
            "headers_to_mask": ["authorization", "x-api-key"],
            "body_keys_to_mask": []
        }
    }

    def __init__(self):
        self.api_logs_dir = SCRIPT_DIR / "api_logs"
        self.api_logs_dir.mkdir(exist_ok=True)

    def log_call(self, service, method, endpoint, request_obj=None, response_obj=None,
                 elapsed_ms=0, error=None):
        """Log an API call with sanitization

        Args:
            service: 'telegram', 'claude', etc.
            method: 'GET', 'POST', etc.
            endpoint: API endpoint URL
            request_obj: dict with 'headers' and 'body' keys
            response_obj: dict with 'status', 'headers', 'body' keys
            elapsed_ms: round-trip time
            error: exception object if failed
        """
        if service not in self.SERVICE_REGISTRY:
            logger.warning(f"APILogger: unknown service '{service}'")
            return

        # Log to text file
        self._log_text(service, method, endpoint, elapsed_ms, error)

        # Log to JSON file
        self._log_json(service, method, endpoint, request_obj, response_obj, elapsed_ms, error)

    def _sanitize_endpoint(self, service, endpoint):
        """Sanitize endpoint by masking sensitive tokens"""
        rules = self.SANITIZATION_RULES.get(service, {})
        if rules.get("endpoint_mask"):
            import re
            endpoint = re.sub(rules["endpoint_mask"], r"bot[MASKED:\g<1>]", endpoint)
        return endpoint

    def _sanitize_headers(self, service, headers):
        """Sanitize headers by masking API keys"""
        if not headers:
            return {}
        headers = dict(headers)  # copy
        rules = self.SANITIZATION_RULES.get(service, {})
        for key in rules.get("headers_to_mask", []):
            for h in list(headers.keys()):
                if h.lower() == key.lower():
                    headers[h] = "[MASKED]"
        return headers

    def _sanitize_body(self, service, body):
        """Sanitize request/response body"""
        if isinstance(body, str) and not body:
            return ""
        if isinstance(body, dict):
            body = dict(body)  # copy
            rules = self.SANITIZATION_RULES.get(service, {})
            for key in rules.get("body_keys_to_mask", []):
                if key in body:
                    body[key] = "[MASKED]"
            return body
        return body

    def _log_text(self, service, method, endpoint, elapsed_ms, error):
        """Log to text file with [EXTERNAL] tag"""
        safe_endpoint = self._sanitize_endpoint(service, endpoint)
        if error:
            logger.error(f"[EXTERNAL] {service.upper()} {method} {safe_endpoint} | ERROR: {type(error).__name__}")
        else:
            logger.info(f"[EXTERNAL] {service.upper()} {method} {safe_endpoint} | {elapsed_ms:.0f}ms")

    def _log_json(self, service, method, endpoint, request_obj, response_obj, elapsed_ms, error):
        """Log to JSON JSONL file for structured querying"""
        json_file_template = self.SERVICE_REGISTRY[service]["json_file"]
        date_str = datetime.now().strftime("%Y-%m-%d")
        json_file = self.api_logs_dir / json_file_template.format(date_str)

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "service": service,
            "method": method,
            "endpoint": self._sanitize_endpoint(service, endpoint),
            "request": {
                "headers": self._sanitize_headers(service, request_obj.get("headers", {}) if request_obj else {}),
                "body": self._sanitize_body(service, request_obj.get("body") if request_obj else None)
            },
            "response": {
                "status": response_obj.get("status") if response_obj else None,
                "headers": self._sanitize_headers(service, response_obj.get("headers", {}) if response_obj else {}),
                "body": self._sanitize_body(service, response_obj.get("body") if response_obj else None)
            } if not error else None,
            "elapsed_ms": round(elapsed_ms, 1),
            "success": not error,
            "error": {"type": type(error).__name__, "message": str(error)} if error else None
        }

        try:
            with open(json_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write API log to {json_file}: {e}")

# Initialize global API logger
api_logger = APILogger()

# Pattern explanations for morning mode
PATTERN_EXPLANATIONS = {
    "Fast and Slow Pointer": "Two pointers at different speeds — detects cycles, finds midpoints, or locates positions in linked lists without extra memory.",
    "Overlapping Intervals": "Sort intervals by start, then merge or count overlaps by comparing current end to next start.",
    "Prefix Sum": "Precompute cumulative sums so any subarray sum becomes O(1): sum(i,j) = prefix[j] - prefix[i-1].",
    "Sliding Window (Fixed)": "Maintain a window of fixed size K — add right element, remove left element each step.",
    "Sliding Window (Variable)": "Expand right pointer until condition breaks, shrink left pointer to restore it. Tracks optimal window.",
    "Two Pointers": "Two indices from opposite ends or same direction — avoids O(n²) nested loops for sorted arrays.",
    "Cyclic Sort": "For arrays with values 1..N, place each number at index (value-1) — then scan for mismatches to find missing/duplicate.",
    "Reversal of Linked List": "Reverse pointers in-place using prev/curr/next — iteratively or in groups of K.",
    "Matrix Manipulation": "Traverse or transform 2D grids — rotation = transpose + reverse rows; spiral = shrink boundaries.",
    "BFS": "Level-by-level traversal using a queue — finds shortest path in unweighted graphs and grid problems.",
    "DFS": "Explore each path fully before backtracking — used for connectivity, cycle detection, and path problems.",
    "Backtracking": "Build solution incrementally, abandon (backtrack) when a constraint is violated — for permutations, combinations, and constraint problems.",
    "Modified Binary Search": "Apply binary search on answer space, not just sorted arrays — used when 'search' can be defined as a monotonic condition.",
    "Bitwise XOR": "XOR of a number with itself is 0, with 0 is itself — finds single/missing numbers without extra space.",
    "Top K Elements": "Use a min-heap of size K — push every element, pop when size exceeds K — result is top K largest.",
    "K-way Merge": "Use a min-heap to merge K sorted lists — always extract the minimum and push its next element.",
    "Two Heaps": "Max-heap for lower half, min-heap for upper half — balance sizes to find median in O(log n).",
    "Monotonic Stack": "Maintain a stack whose elements are always increasing or decreasing — solves 'next greater/smaller element' in O(n).",
    "Trees": "Master level-order (BFS), DFS (inorder/preorder/postorder), construction, path problems, and BST properties.",
    "Dynamic Programming": "Break problem into overlapping subproblems; store results (memoization/tabulation). Identify state, transition, and base case.",
    "Graphs": "Model as nodes + edges. Use DFS/BFS for traversal, topological sort for ordering, union-find for connectivity.",
    "Greedy": "Make locally optimal choice at each step — works when local optimum leads to global optimum (prove by exchange argument).",
    "Design Data Structure": "Combine hash maps, heaps, and linked lists to achieve O(1) or O(log n) for insert/delete/retrieve operations.",
}

def load_tracker():
    """Load DSA tracker from JSON file"""
    try:
        with open(TRACKER_FILE, "r") as f:
            tracker = json.load(f)
        num_problems = len(tracker.get("problems", []))
        streak = tracker.get("metadata", {}).get("streak_days", 0)
        solved = tracker.get("metadata", {}).get("total_problems_solved", 0)
        logger.info(f"Tracker loaded: {num_problems} problems | streak={streak} | solved={solved}")
        return tracker
    except Exception as e:
        logger.error(f"Failed to load tracker: {type(e).__name__}: {e}")
        raise

def save_tracker(tracker):
    """Save DSA tracker to JSON file"""
    try:
        with open(TRACKER_FILE, "w") as f:
            json.dump(tracker, f, indent=2)
        logger.debug(f"Tracker saved successfully")
    except Exception as e:
        logger.error(f"Failed to save tracker: {type(e).__name__}: {e}")
        raise

def get_today_due_problems(tracker):
    """Get active problems due for review today (excludes new problems)"""
    today = datetime.now().strftime("%Y-%m-%d")
    due_problems = [
        p for p in tracker["problems"]
        if p["status"] == "active" and p["next_due"] <= today
    ]
    return due_problems

def get_next_problem(tracker):
    """Get the next new problem to start"""
    for p in tracker["problems"]:
        if p["status"] == "new":
            return p
    return None

def send_telegram_message(text, reply_markup=None):
    """Send message to Telegram with optional inline buttons"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    api_start = time.time()
    try:
        response = requests.post(url, json=payload)
        elapsed_ms = (time.time() - api_start) * 1000

        if response.status_code == 200:
            result = response.json()
            msg_id = result.get("result", {}).get("message_id", "?")
            char_count = len(text)
            logger.info(f"Telegram sendMessage -> 200 OK | msg_id={msg_id} | chars={char_count}")

            # Log API call
            api_logger.log_call(
                service="telegram",
                method="POST",
                endpoint=url,
                request_obj={"headers": {"Content-Type": "application/json"}, "body": payload},
                response_obj={"status": 200, "headers": dict(response.headers), "body": result},
                elapsed_ms=elapsed_ms
            )
            return result
        else:
            logger.error(f"Telegram sendMessage failed: {response.status_code} | {response.text[:100]}")

            # Log API call (failure)
            api_logger.log_call(
                service="telegram",
                method="POST",
                endpoint=url,
                request_obj={"headers": {"Content-Type": "application/json"}, "body": payload},
                response_obj={"status": response.status_code, "headers": dict(response.headers), "body": response.text},
                elapsed_ms=elapsed_ms
            )
            return None
    except Exception as e:
        elapsed_ms = (time.time() - api_start) * 1000
        logger.error(f"Telegram sendMessage exception: {type(e).__name__}: {str(e)[:100]}")
        api_logger.log_call(
            service="telegram",
            method="POST",
            endpoint=url,
            request_obj={"headers": {"Content-Type": "application/json"}, "body": payload},
            elapsed_ms=elapsed_ms,
            error=e
        )
        return None

# Follow-up button sets for different use cases (predefined + Ask More)
FOLLOWUP_SETS = {
    "pattern_explain": [
        [
            {"text": "💻 Java Code", "callback_data": "followup:java:{idx}"},
            {"text": "🎤 Interview Tips", "callback_data": "followup:interview:{idx}"},
            {"text": "🔗 Similar Problems", "callback_data": "followup:similar:{idx}"},
        ],
        [
            {"text": "💬 Ask More", "callback_data": "followup:askmore:{idx}"},
        ],
    ],
    "interview_prep": [
        [
            {"text": "📋 Full Solution", "callback_data": "followup:solution:{idx}"},
            {"text": "⏱️ Complexity", "callback_data": "followup:complexity:{idx}"},
            {"text": "🔄 Try Another", "callback_data": "followup:next:{idx}"},
        ],
        [
            {"text": "💬 Ask More", "callback_data": "followup:askmore:{idx}"},
        ],
    ],
    "approach_check": [
        [
            {"text": "💻 Optimal Code", "callback_data": "followup:solution:{idx}"},
            {"text": "⏱️ Complexity", "callback_data": "followup:complexity:{idx}"},
            {"text": "🎤 Interview Tips", "callback_data": "followup:interview:{idx}"},
        ],
        [
            {"text": "💬 Ask More", "callback_data": "followup:askmore:{idx}"},
        ],
    ],
    "code_template": [
        [
            {"text": "🎤 Interview Tips", "callback_data": "followup:interview:{idx}"},
            {"text": "🔗 Similar Problems", "callback_data": "followup:similar:{idx}"},
            {"text": "📝 Edge Cases", "callback_data": "followup:edgecases:{idx}"},
        ],
        [
            {"text": "💬 Ask More", "callback_data": "followup:askmore:{idx}"},
        ],
    ],
    "compare": [
        [
            {"text": "💡 When to Use Each", "callback_data": "followup:whentouse:{idx}"},
            {"text": "🔗 Practice Problem", "callback_data": "followup:similar:{idx}"},
        ],
        [
            {"text": "💬 Ask More", "callback_data": "followup:askmore:{idx}"},
        ],
    ],
    "stuck": [
        [
            {"text": "📋 Full Solution", "callback_data": "followup:solution:{idx}"},
            {"text": "💡 Another Hint", "callback_data": "followup:hint:{idx}"},
            {"text": "➡️ Next Problem", "callback_data": "followup:next:{idx}"},
        ],
        [
            {"text": "💬 Ask More", "callback_data": "followup:askmore:{idx}"},
        ],
    ],
    "difficulty": [
        [
            {"text": "➡️ Next Problem", "callback_data": "followup:next:{idx}"},
            {"text": "💬 Ask About This", "callback_data": "followup:askmore:{idx}"},
            {"text": "📈 My Stats", "callback_data": "followup:stats:{idx}"},
        ],
    ],
    "stats": [
        [
            {"text": "📈 Weak Areas", "callback_data": "followup:weak:{idx}"},
            {"text": "📝 Create Plan", "callback_data": "followup:plan:{idx}"},
        ],
        [
            {"text": "💬 Ask More", "callback_data": "followup:askmore:{idx}"},
        ],
    ],
    "default": [
        [
            {"text": "➡️ Next Problem", "callback_data": "followup:next:{idx}"},
            {"text": "💬 Ask More", "callback_data": "followup:askmore:{idx}"},
        ],
    ],
}

def create_followup_buttons(problem_index, use_case="default"):
    """Create follow-up buttons for a given use case"""
    idx = str(problem_index)

    # Get the button set for this use case, default to generic
    button_set = FOLLOWUP_SETS.get(use_case, FOLLOWUP_SETS["default"])

    # Replace {idx} placeholders with actual problem index
    formatted_buttons = []
    for row in button_set:
        formatted_row = []
        for btn in row:
            formatted_btn = {
                "text": btn["text"],
                "callback_data": btn["callback_data"].replace("{idx}", idx)
            }
            formatted_row.append(formatted_btn)
        formatted_buttons.append(formatted_row)

    return {"inline_keyboard": formatted_buttons}

def create_adaptive_buttons(problem_index, message_type="default"):
    """Create context-aware inline keyboard based on message type"""
    idx = str(problem_index)

    button_sets = {
        "morning": [
            [
                {"text": "📚 Learn Pattern", "callback_data": f"learn:{idx}"},
                {"text": "📖 More Examples", "callback_data": f"examples:{idx}"},
            ],
            [
                {"text": "💪 I'm Ready", "callback_data": f"ready:{idx}"},
            ],
            [
                {"text": "💬 Ask More", "callback_data": f"askq:{idx}"},
            ]
        ],
        "afternoon": [
            [
                {"text": "💡 Hint", "callback_data": f"hint:{idx}"},
                {"text": "📋 Solution", "callback_data": f"solution:{idx}"},
            ],
            [
                {"text": "❓ Stuck?", "callback_data": f"stuck:{idx}"},
                {"text": "✅ I Solved It", "callback_data": f"solved:{idx}"},
            ],
            [
                {"text": "⏸️ Too Easy", "callback_data": f"toeasy:{idx}"},
                {"text": "❌ Too Hard", "callback_data": f"tohard:{idx}"},
            ],
            [
                {"text": "➡️ Next Question", "callback_data": f"nextq:{idx}"},
                {"text": "💬 Ask More", "callback_data": f"askq:{idx}"},
            ]
        ],
        "review": [
            [
                {"text": "💡 Hint", "callback_data": f"hint:{idx}"},
                {"text": "📋 Solution", "callback_data": f"solution:{idx}"},
            ],
            [
                {"text": "✅ I Know It", "callback_data": f"easy:{idx}"},
                {"text": "⏸️ Medium", "callback_data": f"medium:{idx}"},
                {"text": "❌ Need Practice", "callback_data": f"hard:{idx}"},
            ],
            [
                {"text": "💬 Ask More", "callback_data": f"askq:{idx}"},
            ]
        ],
        "evening": [
            [
                {"text": "📊 My Stats", "callback_data": f"stats:{idx}"},
                {"text": "📈 Weak Areas", "callback_data": f"weak:{idx}"},
            ],
            [
                {"text": "📝 Create Plan", "callback_data": f"plan:{idx}"},
            ],
            [
                {"text": "💬 Ask More", "callback_data": f"askq:{idx}"},
            ]
        ],
        "night": [
            [
                {"text": "📊 My Stats", "callback_data": f"stats:{idx}"},
                {"text": "➡️ Next Question", "callback_data": f"nextq:{idx}"},
            ],
            [
                {"text": "💬 Ask More", "callback_data": f"askq:{idx}"},
            ]
        ],
        "default": [
            [
                {"text": "✅ Easy", "callback_data": f"easy:{idx}"},
                {"text": "⏸️ Medium", "callback_data": f"medium:{idx}"},
                {"text": "❌ Hard", "callback_data": f"hard:{idx}"},
            ],
            [
                {"text": "💡 Hint", "callback_data": f"hint:{idx}"},
                {"text": "📋 Solution", "callback_data": f"solution:{idx}"},
                {"text": "⏭️ Skip", "callback_data": f"skip:{idx}"},
            ],
            [
                {"text": "🏆 Mastered", "callback_data": f"mastered:{idx}"},
            ],
            [
                {"text": "💬 Ask More", "callback_data": f"askq:{idx}"},
            ]
        ]
    }

    buttons = button_sets.get(message_type, button_sets["default"])
    return {"inline_keyboard": buttons}

def generate_afternoon_message(problem):
    """Generate afternoon solving session message with step-by-step approach + pseudocode"""
    client = Anthropic(api_key=CLAUDE_API_KEY)
    api_start = time.time()

    prompt = f"""Generate a detailed afternoon DSA solving session guide. Be specific and practical.

Problem: {problem['title']} (LeetCode #{problem['leetcode_number']})
Pattern: {problem['pattern']}
Difficulty: {problem['difficulty']}

Include:
1. Key Insight: What's the core trick to solving this?
2. Step-by-Step Approach: List 3-4 concrete steps
3. Java Code Skeleton: Show skeleton code in JAVA (structure only, 5-8 lines max)
4. End with: "Ready to solve it? Tap a difficulty button below after you're done!"

Keep it under 200 words. Make it actionable. Use JAVA for all code."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        elapsed = (time.time() - api_start) * 1000
        usage = response.usage
        logger.info(f"Claude API (afternoon): {usage.input_tokens} in | {usage.output_tokens} out | {elapsed:.0f}ms")

        # Log API call
        api_logger.log_call(
            service="claude",
            method="POST",
            endpoint="https://api.anthropic.com/v1/messages",
            request_obj={
                "headers": {"x-api-key": CLAUDE_API_KEY, "Content-Type": "application/json"},
                "body": {"model": "claude-sonnet-4-6", "max_tokens": 300, "messages": [{"role": "user", "content": prompt}]}
            },
            response_obj={
                "status": 200,
                "headers": {},
                "body": {"tokens_in": usage.input_tokens, "tokens_out": usage.output_tokens, "content": response.content[0].text}
            },
            elapsed_ms=elapsed
        )

        return response.content[0].text
    except Exception as e:
        elapsed = (time.time() - api_start) * 1000
        logger.error(f"Claude API failed: {type(e).__name__}: {str(e)[:100]} | {elapsed:.0f}ms")

        # Log API call (failure)
        api_logger.log_call(
            service="claude",
            method="POST",
            endpoint="https://api.anthropic.com/v1/messages",
            request_obj={
                "headers": {"x-api-key": CLAUDE_API_KEY, "Content-Type": "application/json"},
                "body": {"model": "claude-sonnet-4-6", "max_tokens": 300, "messages": [{"role": "user", "content": prompt}]}
            },
            elapsed_ms=elapsed,
            error=e
        )
        raise

def generate_evening_message(tracker, problem):
    """Generate evening reminder message"""
    due_problems = get_today_due_problems(tracker)
    streak = tracker["metadata"]["streak_days"]
    total_solved = tracker["metadata"]["total_problems_solved"]

    return f"""⏰ Time for your 1-hour DSA session, Manoj!

📊 Today's Status:
  • Due for SRS review: {len(due_problems)} problem(s)
  • New problem: {problem['title']} ({problem['difficulty']})
  • Streak: {streak} days 🔥
  • Total solved: {total_solved}

This pattern ({problem['pattern']}) is essential for interviews. Let's go! 💪"""

def generate_night_summary(tracker, problem, difficulty=None):
    """Generate night summary with tomorrow's preview using Claude"""
    client = Anthropic(api_key=CLAUDE_API_KEY)
    api_start = time.time()

    pattern = problem['pattern']
    similar_problems_same_pattern = [
        p['title'] for p in tracker['problems']
        if p['pattern'] == pattern and p['id'] != problem['id']
    ][:2]

    prompt = f"""Generate a concise night summary for DSA practice. Include:
1. What was practiced today
2. Pattern name and approach (2-3 lines)
3. List 2-3 similar problems in the same pattern
4. Java code template for this pattern

Problem practiced: {problem['title']}
Pattern: {pattern}
Difficulty: {problem['difficulty']}
Similar problems: {', '.join(similar_problems_same_pattern) if similar_problems_same_pattern else 'N/A'}

Keep under 200 words. Format as a summary. Use JAVA for all code templates."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )
        elapsed = (time.time() - api_start) * 1000
        usage = response.usage
        logger.info(f"Claude API (night): {usage.input_tokens} in | {usage.output_tokens} out | {elapsed:.0f}ms")

        # Log API call
        api_logger.log_call(
            service="claude",
            method="POST",
            endpoint="https://api.anthropic.com/v1/messages",
            request_obj={
                "headers": {"x-api-key": CLAUDE_API_KEY, "Content-Type": "application/json"},
                "body": {"model": "claude-sonnet-4-6", "max_tokens": 300, "messages": [{"role": "user", "content": prompt}]}
            },
            response_obj={
                "status": 200,
                "headers": {},
                "body": {"tokens_in": usage.input_tokens, "tokens_out": usage.output_tokens, "content": response.content[0].text}
            },
            elapsed_ms=elapsed
        )

        return f"""🌙 Night Summary - Day {tracker['metadata']['total_problems_solved'] + 1}

{response.content[0].text}

✨ Tomorrow: Onward to the next problem!"""
    except Exception as e:
        elapsed = (time.time() - api_start) * 1000
        logger.error(f"Claude API failed: {type(e).__name__}: {str(e)[:100]} | {elapsed:.0f}ms")

        # Log API call (failure)
        api_logger.log_call(
            service="claude",
            method="POST",
            endpoint="https://api.anthropic.com/v1/messages",
            request_obj={
                "headers": {"x-api-key": CLAUDE_API_KEY, "Content-Type": "application/json"},
                "body": {"model": "claude-sonnet-4-6", "max_tokens": 300, "messages": [{"role": "user", "content": prompt}]}
            },
            elapsed_ms=elapsed,
            error=e
        )
        raise

def update_tracker_after_review(tracker, problem_id, difficulty):
    """Update tracker using SM-2 algorithm after a review"""
    today = datetime.now().strftime("%Y-%m-%d")

    for p in tracker["problems"]:
        if p["id"] == problem_id:
            old_interval = p["interval_days"]
            old_ease = p["ease_factor"]
            p["last_reviewed"] = today
            p["times_reviewed"] += 1

            if difficulty == "easy":
                p["interval_days"] = max(1, int(p["interval_days"] * 2.5))
                p["ease_factor"] = min(2.5, p["ease_factor"] + 0.1)
            elif difficulty == "medium":
                p["interval_days"] = max(1, int(p["interval_days"] * p["ease_factor"]))
            elif difficulty == "hard":
                p["interval_days"] = 1
                p["ease_factor"] = max(1.3, p["ease_factor"] - 0.2)

            next_due_date = datetime.now() + timedelta(days=p["interval_days"])
            p["next_due"] = next_due_date.strftime("%Y-%m-%d")

            if p["status"] == "new":
                p["status"] = "active"

            logger.info(f"SM-2 update: {p['title']} | {difficulty} | interval {old_interval}→{p['interval_days']} days | ease {old_ease:.2f}→{p['ease_factor']:.2f} | next_due={p['next_due']}")
            break

    tracker["metadata"]["total_problems_solved"] = len([
        p for p in tracker["problems"] if p["times_reviewed"] > 0
    ])

    # Streak tracking: increment on new days, reset if >1 day gap
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    last_updated = tracker["metadata"].get("last_updated", "")

    if last_updated == today:
        pass  # Already counted this day
    elif last_updated == yesterday_str:
        tracker["metadata"]["streak_days"] = tracker["metadata"].get("streak_days", 0) + 1
    else:
        tracker["metadata"]["streak_days"] = 1

    tracker["metadata"]["last_updated"] = today

def morning_mode():
    """Send early morning prep: pattern explanation + today's problem + warm-up"""
    tracker = load_tracker()
    next_problem = get_next_problem(tracker)
    due_reviews = get_today_due_problems(tracker)

    if not next_problem:
        send_telegram_message("🎉 All Week 1 problems covered! Move to Week 2.")
        return

    pattern = next_problem['pattern']
    pattern_explanation = PATTERN_EXPLANATIONS.get(pattern, "Master this pattern for interview success.")

    # Find 2 related problems in same pattern
    similar = [p for p in tracker['problems'] if p['pattern'] == pattern and p['id'] != next_problem['id']][:2]
    similar_list = "\n".join([f"  • {p['title']}" for p in similar]) if similar else "  None yet"

    reviews_line = f"🔄 Reviews due today: {len(due_reviews)} problem(s) to revisit\n" if due_reviews else ""

    message = f"""🌅 Good Morning, Manoj!

📚 Today's Pattern: {pattern}
What it means: {pattern_explanation}

🎯 Main Problem: {next_problem['title']} (LeetCode #{next_problem['leetcode_number']})
Difficulty: {next_problem['difficulty']}

🔗 LeetCode: {next_problem['leetcode_url']}

📖 Related problems in this pattern:
{similar_list}

Warm-up tip: Review the pattern approach before solving the main problem.

{reviews_line}Streak: {tracker['metadata']['streak_days']} days | Total solved: {tracker['metadata']['total_problems_solved']}"""

    next_problem_index = tracker["problems"].index(next_problem)
    buttons = create_adaptive_buttons(next_problem_index, message_type="morning")
    send_telegram_message(message, reply_markup=buttons)
    print(f"✅ Morning prep sent for pattern: {pattern}")

def generate_review_message(problem):
    """Generate a message for a problem due for SRS review"""
    pattern = problem["pattern"]
    hint = PATTERN_EXPLANATIONS.get(pattern, "Recall the core technique before looking it up.")
    return (
        f"📅 SRS Review: <b>{problem['title']}</b>\n"
        f"LeetCode #{problem['leetcode_number']} | {problem['difficulty']} | {problem['pattern']}\n\n"
        f"💡 Pattern hint: {hint}\n\n"
        f"🔗 {problem['leetcode_url']}\n\n"
        f"Reviewed {problem['times_reviewed']}× | Current interval: {problem['interval_days']} day(s)\n\n"
        f"Solve it from memory, then rate how it went:"
    )

def generate_hint_message(problem):
    """Generate a targeted hint via Claude. Mentor style — no solution spoilers."""
    client = Anthropic(api_key=CLAUDE_API_KEY)
    prompt = f"""Give a targeted hint for this DSA problem. Do NOT reveal the solution or write any code.

Problem: {problem['title']} (LeetCode #{problem['leetcode_number']})
Pattern: {problem['pattern']}
Difficulty: {problem['difficulty']}

Provide exactly:
1. One Socratic question to guide their thinking
2. A conceptual nudge (1-2 lines, no code)
3. Which data structure to consider and why (1 line)

Under 100 words. Be a mentor, not a spoiler."""

    api_start = time.time()
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}]
        )
        elapsed_ms = (time.time() - api_start) * 1000
        usage = response.usage
        logger.info(f"Claude API (hint): {usage.input_tokens} in | {usage.output_tokens} out | {elapsed_ms:.0f}ms")
        api_logger.log_call(
            service="claude", method="POST",
            endpoint="https://api.anthropic.com/v1/messages",
            request_obj={"headers": {"x-api-key": "[MASKED]", "Content-Type": "application/json"},
                         "body": {"model": "claude-sonnet-4-6", "max_tokens": 150, "messages": [{"role": "user", "content": prompt}]}},
            response_obj={"status": 200, "headers": {},
                          "body": {"tokens_in": usage.input_tokens, "tokens_out": usage.output_tokens, "content": response.content[0].text}},
            elapsed_ms=elapsed_ms
        )
        return f"💡 <b>Hint — {problem['title']}:</b>\n\n{response.content[0].text}"
    except Exception as e:
        elapsed_ms = (time.time() - api_start) * 1000
        logger.error(f"Claude hint API error: {type(e).__name__}: {e}")
        api_logger.log_call(
            service="claude", method="POST",
            endpoint="https://api.anthropic.com/v1/messages",
            request_obj={"headers": {"x-api-key": "[MASKED]", "Content-Type": "application/json"},
                         "body": {"model": "claude-sonnet-4-6", "max_tokens": 150, "messages": []}},
            elapsed_ms=elapsed_ms, error=e
        )
        hint_text = PATTERN_EXPLANATIONS.get(problem["pattern"], "Think about the pattern's core technique.")
        return f"💡 <b>Hint — {problem['title']}:</b>\n\n{hint_text}\n\n<i>(Claude unavailable — showing pattern hint)</i>"

def convert_markdown_to_html(text):
    """Convert markdown code blocks to HTML-safe format for Telegram"""
    import re
    # Remove markdown code block markers and keep the code
    text = re.sub(r'```java\n', '<pre><code>', text)
    text = re.sub(r'```\n', '</code></pre>', text)
    text = re.sub(r'```', '</code></pre>', text)
    # Convert markdown headers to bold
    text = re.sub(r'^## (.+)$', r'<b>\1</b>', text, flags=re.MULTILINE)
    # Convert markdown bold/italic
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'_(.+?)_', r'<i>\1</i>', text)
    return text

def generate_solution_preview(problem):
    """Generate interview-ready solution with Java code, complexity, and explanation"""
    client = Anthropic(api_key=CLAUDE_API_KEY)
    prompt = f"""Provide an interview-ready solution for this DSA problem in Java.

Problem: {problem['title']} (LeetCode #{problem['leetcode_number']})
Pattern: {problem['pattern']}
Difficulty: {problem['difficulty']}
URL: {problem['leetcode_url']}

Format your response EXACTLY as follows:

## APPROACH
[1-2 sentences explaining the core idea and why it works]

## KEY INSIGHT
[1-2 sentences about the main trick/observation]

## JAVA CODE
```java
class Solution {{
    public [RETURN_TYPE] [METHOD_NAME]([PARAMETERS]) {{
        // Best solution in Java
        // [Code here]
    }}
}}
```

## TIME & SPACE COMPLEXITY
- Time: O(...)
- Space: O(...)

## INTERVIEW EXPLANATION
When explaining this in an interview:
1. [First point to mention]
2. [Second point to mention]
3. [Third point to mention]

Keep code readable (max 15 lines). Format for mobile viewing."""

    api_start = time.time()
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        elapsed_ms = (time.time() - api_start) * 1000
        usage = response.usage
        logger.info(f"Claude API (solution): {usage.input_tokens} in | {usage.output_tokens} out | {elapsed_ms:.0f}ms")
        api_logger.log_call(
            service="claude", method="POST",
            endpoint="https://api.anthropic.com/v1/messages",
            request_obj={"headers": {"x-api-key": "[MASKED]", "Content-Type": "application/json"},
                         "body": {"model": "claude-sonnet-4-6", "max_tokens": 800, "messages": [{"role": "user", "content": prompt}]}},
            response_obj={"status": 200, "headers": {},
                          "body": {"tokens_in": usage.input_tokens, "tokens_out": usage.output_tokens, "content": response.content[0].text}},
            elapsed_ms=elapsed_ms
        )
        solution_text = convert_markdown_to_html(response.content[0].text)
        return f"📋 <b>Solution — {problem['title']}</b>\n\n{solution_text}"
    except Exception as e:
        elapsed_ms = (time.time() - api_start) * 1000
        logger.error(f"Claude solution API error: {type(e).__name__}: {e}")
        api_logger.log_call(
            service="claude", method="POST",
            endpoint="https://api.anthropic.com/v1/messages",
            request_obj={"headers": {"x-api-key": "[MASKED]", "Content-Type": "application/json"},
                         "body": {"model": "claude-sonnet-4-6", "max_tokens": 800, "messages": []}},
            elapsed_ms=elapsed_ms, error=e
        )
        return f"📋 <b>Solution — {problem['title']}:</b>\n\n<i>Claude API unavailable. See LeetCode discussions: {problem['leetcode_url']}</i>"

def check_pattern_completion(tracker, problem):
    """Returns (True, count) if all problems in this pattern have been attempted."""
    pattern = problem["pattern"]
    pattern_problems = [p for p in tracker["problems"] if p["pattern"] == pattern]
    all_attempted = all(p["status"] != "new" for p in pattern_problems)
    return all_attempted, len(pattern_problems)

def afternoon_mode():
    """Send afternoon session reminder: SRS reviews first, then today's new problem"""
    tracker = load_tracker()
    due_reviews = get_today_due_problems(tracker)
    new_problem = get_next_problem(tracker)

    # Send review messages first (up to 3 to avoid overwhelming)
    for review in due_reviews[:3]:
        msg = generate_review_message(review)
        review_index = tracker["problems"].index(review)
        buttons = create_adaptive_buttons(review_index, message_type="review")
        send_telegram_message(msg, reply_markup=buttons)
        logger.info(f"Review message sent: {review['title']}")

    # Then send today's new problem
    if not new_problem:
        if not due_reviews:
            send_telegram_message("🎉 All problems for today are covered!")
        return

    try:
        message = generate_afternoon_message(new_problem)
    except Exception as e:
        logger.error(f"Claude API error: {e}")
        message = f"📝 Problem: {new_problem['title']}\n💡 Pattern: {new_problem['pattern']}\n🔗 {new_problem['leetcode_url']}"

    new_problem_index = tracker["problems"].index(new_problem)
    buttons = create_adaptive_buttons(new_problem_index, message_type="afternoon")
    send_telegram_message(message, reply_markup=buttons)
    print(f"✅ Afternoon session reminder sent for: {new_problem['title']}")

def evening_mode():
    """Send evening SRS review: problems due today + check if main problem was solved"""
    tracker = load_tracker()
    due_problems = get_today_due_problems(tracker)
    next_problem = get_next_problem(tracker)

    if not next_problem:
        send_telegram_message("🎉 All problems for today are covered! Rest well.")
        return

    due_list = "\n".join([f"  • {p['title']} ({p['pattern']})" for p in due_problems]) if due_problems else "  None - all caught up!"

    message = f"""📖 Evening Review Session

Problems due for SRS review today:
{due_list}

Today's main problem: {next_problem['title']}
Status: Check if you solved and rated it with the afternoon button!

Streak: {tracker['metadata']['streak_days']} days
Total solved: {tracker['metadata']['total_problems_solved']}

Go through the review problems and try to recall the approach from memory."""

    next_problem_index = tracker["problems"].index(next_problem)
    buttons = create_adaptive_buttons(next_problem_index, message_type="evening")
    send_telegram_message(message, reply_markup=buttons)
    print(f"✅ Evening review reminder sent")

def night_mode():
    """Send night summary: pattern recap + pseudocode + similar problems + tomorrow"""
    tracker = load_tracker()
    next_problem = get_next_problem(tracker)

    if not next_problem:
        send_telegram_message("🌙 Amazing week! Rest well, champion.")
        return

    # Find tomorrow's problem (second new problem)
    all_new = [p for p in tracker["problems"] if p["status"] == "new"]
    tomorrow_problem = all_new[1] if len(all_new) > 1 else None

    try:
        message = generate_night_summary(tracker, next_problem)
    except Exception as e:
        print(f"Claude API error: {e}")
        message = f"🌙 Night Summary\nPattern: {next_problem['pattern']}\nTomorrow: Another step forward!"

    next_problem_index = tracker["problems"].index(next_problem)
    buttons = create_adaptive_buttons(next_problem_index, message_type="night")
    send_telegram_message(message, reply_markup=buttons)

    # Send tomorrow's preview
    if tomorrow_problem:
        preview = (
            f"👀 <b>Tomorrow's Preview:</b>\n"
            f"<b>{tomorrow_problem['title']}</b> (LeetCode #{tomorrow_problem['leetcode_number']})\n"
            f"Pattern: {tomorrow_problem['pattern']} | {tomorrow_problem['difficulty']}\n\n"
            f"Sleep well — a focused mind solves faster. 🌙"
        )
        send_telegram_message(preview)

    print(f"✅ Night summary sent")

def answer_callback_query(callback_query_id, text=""):
    """Dismiss the loading spinner on a tapped button"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery"
    api_start = time.time()
    payload = {"callback_query_id": callback_query_id, "text": text}

    try:
        response = requests.post(url, json=payload)
        elapsed_ms = (time.time() - api_start) * 1000

        # Log API call
        api_logger.log_call(
            service="telegram",
            method="POST",
            endpoint=url,
            request_obj={"headers": {"Content-Type": "application/json"}, "body": payload},
            response_obj={"status": response.status_code, "headers": dict(response.headers), "body": response.text},
            elapsed_ms=elapsed_ms
        )
    except Exception as e:
        elapsed_ms = (time.time() - api_start) * 1000
        logger.error(f"answerCallbackQuery exception: {type(e).__name__}: {str(e)[:100]}")
        api_logger.log_call(
            service="telegram",
            method="POST",
            endpoint=url,
            request_obj={"headers": {"Content-Type": "application/json"}, "body": payload},
            elapsed_ms=elapsed_ms,
            error=e
        )

def handle_button_callback(callback_data):
    """Process button clicks. Handles new (action:index), old-slug, and bare-action formats."""
    tracker = load_tracker()

    parts = callback_data.split(":", 1)
    action_raw = parts[0]
    param = parts[1] if len(parts) > 1 else None

    # Normalize old action names to short form
    action_map = {
        "difficulty_easy": "easy", "difficulty_medium": "medium",
        "difficulty_hard": "hard", "skip_problem": "skip",
    }
    action = action_map.get(action_raw, action_raw)

    # Resolve problem
    if param is None:
        problem = get_next_problem(tracker)
    elif param.isdigit():
        idx = int(param)
        problem = tracker["problems"][idx] if idx < len(tracker["problems"]) else None
    else:
        problem = next((p for p in tracker["problems"] if p["id"] == param), None)

    if not problem:
        return None

    # Prevent stale buttons from re-scheduling an archived problem
    # But allow hint, solution, stats, weak, learn, examples to always work (read-only actions)
    if problem.get("status") == "mastered" and action not in ("hint", "solution", "stats", "weak", "learn", "examples"):
        return None

    if action in ("easy", "medium", "hard"):
        update_tracker_after_review(tracker, problem["id"], action)
        save_tracker(tracker)
        for p in tracker["problems"]:
            if p["id"] == problem["id"]:
                return (problem["title"], p["interval_days"], action, problem["pattern"])
    elif action == "skip":
        return (problem["title"], None, "skip", None)
    elif action == "hint":
        return (problem["title"], None, "hint", problem)
    elif action == "mastered":
        for p in tracker["problems"]:
            if p["id"] == problem["id"]:
                p["status"] = "mastered"
                break
        save_tracker(tracker)
        return (problem["title"], None, "mastered", None)
    elif action == "solution":
        return (problem["title"], None, "solution", problem)
    elif action == "stuck":
        return (problem["title"], None, "stuck", problem)
    elif action == "solved":
        return (problem["title"], None, "solved", None)
    elif action == "toeasy":
        return (problem["title"], None, "toeasy", None)
    elif action == "tohard":
        return (problem["title"], None, "tohard", None)
    elif action == "learn":
        return (problem["title"], None, "learn", problem)
    elif action == "examples":
        return (problem["title"], None, "examples", problem)
    elif action == "ready":
        return (problem["title"], None, "ready", None)
    elif action == "stats":
        return (problem["title"], None, "stats", tracker)
    elif action == "weak":
        return (problem["title"], None, "weak", tracker)
    elif action == "plan":
        return (problem["title"], None, "plan", tracker)
    elif action == "followup":
        # Parse followup:sub_action:idx format
        sub_parts = callback_data.split(":", 2)
        sub_action = sub_parts[1] if len(sub_parts) > 1 else "askmore"
        return (problem["title"], None, f"followup_{sub_action}", problem)
    elif action == "nextq":
        return (problem["title"], None, "nextq", None)
    elif action == "askq":
        return (problem["title"], None, "askq", None)

    return None

def get_learning_stats(tracker):
    """Calculate and format learning progress statistics"""
    total = len(tracker["problems"])
    active = len([p for p in tracker["problems"] if p["status"] == "active"])
    new = len([p for p in tracker["problems"] if p["status"] == "new"])
    mastered = len([p for p in tracker["problems"] if p["status"] == "mastered"])

    total_reviews = sum(p["times_reviewed"] for p in tracker["problems"])
    avg_ease = sum(p["ease_factor"] for p in tracker["problems"]) / total if total > 0 else 0

    streak = tracker["metadata"]["streak_days"]
    solved = tracker["metadata"]["total_problems_solved"]

    return f"""📊 <b>Your Learning Stats</b>

🎯 Progress:
  • Total problems: {total}
  • New: {new} | Active: {active} | Mastered: {mastered}
  • Total reviews: {total_reviews}
  • Avg. ease factor: {avg_ease:.2f}/2.5

🔥 Streak: {streak} days
✅ Problems solved: {solved}
⏱️ Last updated: {tracker['metadata'].get('last_updated', 'N/A')}"""

def analyze_weak_areas(tracker):
    """Identify patterns and problems user struggles with"""
    if not tracker["problems"]:
        return "📈 No data yet. Keep practicing! 💪"

    # Find problems with low ease factor or high review count without mastery
    weak_problems = [
        p for p in tracker["problems"]
        if p["status"] != "mastered" and (p["ease_factor"] < 1.5 or p["times_reviewed"] > 3)
    ]

    # Group by pattern
    weak_patterns = {}
    for p in weak_problems:
        pattern = p["pattern"]
        weak_patterns[pattern] = weak_patterns.get(pattern, 0) + 1

    if not weak_patterns:
        return "🌟 <b>You're doing great!</b>\n\nNo weak areas detected. All patterns are looking solid. Keep up the momentum! 💪"

    weak_list = "\n".join([f"  • {p}: {count} problem(s) to revisit" for p, count in sorted(weak_patterns.items(), key=lambda x: x[1], reverse=True)])
    return f"""📈 <b>Areas to Focus On</b>

Based on your performance:
{weak_list}

💡 Tip: Revisit these patterns by solving similar problems. Each attempt strengthens your understanding!"""

def get_followup_buttons(tracker, use_case="default"):
    """Get follow-up buttons for the next problem (generic helper)"""
    next_p = get_next_problem(tracker)
    if not next_p:
        return None
    idx = tracker["problems"].index(next_p)
    return create_followup_buttons(idx, use_case)

def log_question(tracker, intent, question_text, problem_context):
    """Log a user question to the tracker for analysis"""
    if "question_log" not in tracker:
        tracker["question_log"] = []

    tracker["question_log"].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": datetime.now().isoformat(),
        "intent": intent,
        "question": question_text[:200],
        "problem_context": problem_context
    })

    save_tracker(tracker)
    logger.info(f"Question logged: {intent} | {problem_context}")

def detect_intent(text):
    """Detect user intent from text message. Specific intents checked first."""
    text_lower = text.lower()

    # Order matters: more specific intents first (catch detailed queries before generic)
    intents = {
        # 6 new real-world Q&A use cases (specific)
        "pattern_explain": ["what is", "explain", "how does", "how do i use", "tell me about", "what are"],
        "interview_prep": ["interview", "talk about", "explain to", "how would i say", "how to present"],
        "approach_check": ["is this optimal", "better way", "better approach", "my approach", "is there a better"],
        "code_template": ["java code", "template", "show code", "skeleton", "boilerplate", "java template"],
        "compare": ["difference between", " vs ", " versus ", "compare", "which is better"],
        "simplify": ["don't understand problem", "explain problem", "simpler", "what does it want", "clarify"],
        # Original intents (generic)
        "stuck": ["stuck", "help", "guide", "hint", "step", "how do i", "don't understand"],
        "solution": ["show solution", "solution please", "reveal", "answer", "correct answer"],
        "difficulty": ["too easy", "too hard", "easy", "hard", "harder", "easier"],
        "stats": ["stats", "progress", "how much", "my stats", "how many"],
        "weak": ["weak", "struggle", "bad at", "difficult pattern", "hard pattern"],
        "plan": ["plan", "schedule", "what should", "recommend", "suggest"],
        "done": ["done", "solved", "completed", "finished", "i solved"],
        "skip": ["skip", "next", "different", "another problem"],
    }

    for intent, keywords in intents.items():
        if any(kw in text_lower for kw in keywords):
            return intent

    return "question"

def handle_pattern_explain(text, problem):
    """Explain the pattern for the current problem with concept + when to use + pitfalls"""
    client = Anthropic(api_key=CLAUDE_API_KEY)
    api_start = time.time()

    prompt = f"""Explain the pattern for this DSA problem. Be clear and practical.

Problem: {problem['title']} (LeetCode #{problem['leetcode_number']})
Pattern: {problem['pattern']}
Difficulty: {problem['difficulty']}

Include:
1. What is this pattern? (concept in 1-2 sentences)
2. When to use it? (practical scenarios)
3. Key pitfalls? (1-2 common mistakes)
4. Quick Java skeleton (5-8 lines, structure only)

Keep under 200 words. Make it actionable."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=250,
            messages=[{"role": "user", "content": prompt}]
        )
        elapsed = (time.time() - api_start) * 1000
        logger.info(f"Claude API (pattern_explain): {elapsed:.0f}ms")
        return f"📚 <b>{problem['pattern']} Pattern Explained</b>\n\n{response.content[0].text}"
    except Exception as e:
        logger.error(f"Claude pattern_explain error: {e}")
        explanation = PATTERN_EXPLANATIONS.get(problem["pattern"], "Master this pattern for interview success.")
        return f"📚 <b>{problem['pattern']} Pattern</b>\n\n{explanation}"

def handle_interview_prep(problem):
    """Generate interview talking points for the problem"""
    client = Anthropic(api_key=CLAUDE_API_KEY)
    api_start = time.time()

    prompt = f"""Generate 3 clear talking points for explaining this problem in an interview.

Problem: {problem['title']} (LeetCode #{problem['leetcode_number']})
Pattern: {problem['pattern']}
Difficulty: {problem['difficulty']}

Format:
1. [Point 1]: Why this approach works
2. [Point 2]: Time/Space complexity explanation
3. [Point 3]: Common follow-up or edge case

Conversational tone, 1-2 sentences each. Under 150 words."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        elapsed = (time.time() - api_start) * 1000
        logger.info(f"Claude API (interview_prep): {elapsed:.0f}ms")
        return f"🎤 <b>Interview Talking Points</b>\n\n{response.content[0].text}"
    except Exception as e:
        logger.error(f"Claude interview_prep error: {e}")
        return "🎤 <b>Interview Tips</b>\n\nFocus on: approach, complexity, and edge cases. Practice explaining clearly!"

def handle_approach_check(problem):
    """Analyze if the approach is optimal"""
    client = Anthropic(api_key=CLAUDE_API_KEY)
    api_start = time.time()

    prompt = f"""Analyze the optimal approach for this DSA problem.

Problem: {problem['title']} (LeetCode #{problem['leetcode_number']})
Pattern: {problem['pattern']}
Difficulty: {problem['difficulty']}

Provide:
1. Best pattern to use and why
2. Why alternatives are worse (1-2 lines)
3. Time/Space complexity (brief)

Under 150 words. Be direct."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=180,
            messages=[{"role": "user", "content": prompt}]
        )
        elapsed = (time.time() - api_start) * 1000
        logger.info(f"Claude API (approach_check): {elapsed:.0f}ms")
        return f"✅ <b>Optimal Approach</b>\n\n{response.content[0].text}"
    except Exception as e:
        logger.error(f"Claude approach_check error: {e}")
        return "✅ <b>Approach</b>\n\nUse the pattern specified for this problem. It's optimal for this category."

def handle_code_template(problem):
    """Provide a Java code skeleton/template"""
    client = Anthropic(api_key=CLAUDE_API_KEY)
    api_start = time.time()

    prompt = f"""Provide a clean Java implementation template/skeleton for this problem.

Problem: {problem['title']} (LeetCode #{problem['leetcode_number']})
Pattern: {problem['pattern']}

Output ONLY the Java code (class + method skeleton, 10-15 lines). Include brief comments.
No explanations, just clean, ready-to-fill-in code."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=180,
            messages=[{"role": "user", "content": prompt}]
        )
        elapsed = (time.time() - api_start) * 1000
        logger.info(f"Claude API (code_template): {elapsed:.0f}ms")
        return f"💻 <b>Java Code Template</b>\n\n<pre><code>{response.content[0].text}</code></pre>"
    except Exception as e:
        logger.error(f"Claude code_template error: {e}")
        return "💻 <b>Java Template</b>\n\nStart with: class Solution { ... } and fill in the logic."

def handle_compare(text, problem):
    """Compare two concepts mentioned in the text"""
    client = Anthropic(api_key=CLAUDE_API_KEY)
    api_start = time.time()

    prompt = f"""Compare the two DSA concepts mentioned in the user's question.
User asked: {text}
Current problem: {problem['title']} ({problem['pattern']})

Provide side-by-side:
1. Concept A: When to use, key difference
2. Concept B: When to use, key difference
3. Example problem for each

Under 200 words. Be concise."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=220,
            messages=[{"role": "user", "content": prompt}]
        )
        elapsed = (time.time() - api_start) * 1000
        logger.info(f"Claude API (compare): {elapsed:.0f}ms")
        return f"⚖️ <b>Comparison</b>\n\n{response.content[0].text}"
    except Exception as e:
        logger.error(f"Claude compare error: {e}")
        return "⚖️ <b>Comparison</b>\n\nCompare concepts side-by-side in your notes. Practice both!"

def handle_problem_simplify(problem):
    """Restate the problem in the simplest terms"""
    client = Anthropic(api_key=CLAUDE_API_KEY)
    api_start = time.time()

    prompt = f"""Restate this problem in the SIMPLEST possible terms with a tiny concrete example.

Problem: {problem['title']} (LeetCode #{problem['leetcode_number']})
Description: {problem.get('description', 'See LeetCode')}

Format:
1. Simplest explanation (no jargon, 2 sentences max)
2. Concrete example: input → output (very simple numbers)

Under 100 words."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=140,
            messages=[{"role": "user", "content": prompt}]
        )
        elapsed = (time.time() - api_start) * 1000
        logger.info(f"Claude API (problem_simplify): {elapsed:.0f}ms")
        return f"🎯 <b>Simple Explanation</b>\n\n{response.content[0].text}"
    except Exception as e:
        logger.error(f"Claude problem_simplify error: {e}")
        return "🎯 <b>Simple Explanation</b>\n\nBreak the problem into tiny input/output examples."

def handle_stuck_message(problem, tracker):
    """Generate guided hint for stuck user - Claude powered"""
    client = Anthropic(api_key=CLAUDE_API_KEY)
    api_start = time.time()

    prompt = f"""User is stuck on this DSA problem. Give a GUIDED hint only - NO CODE, NO SOLUTION.
Be a helpful mentor. Ask Socratic questions to guide their thinking.

Problem: {problem['title']} (LeetCode #{problem['leetcode_number']})
Pattern: {problem['pattern']}
Difficulty: {problem['difficulty']}

Format:
1. One guiding question to start their thinking
2. A conceptual nudge (1-2 lines, no code)
3. Data structure hint: which one to consider?

Keep under 100 words. Be encouraging."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}]
        )
        elapsed = (time.time() - api_start) * 1000
        logger.info(f"Claude API (adaptive hint): {elapsed:.0f}ms")
        return f"🤝 <b>Let's work through this together</b>\n\n{response.content[0].text}\n\n💪 You've got this! Take your time."
    except Exception as e:
        logger.error(f"Claude adaptive hint error: {e}")
        hint = PATTERN_EXPLANATIONS.get(problem["pattern"], "Think about the core pattern.")
        return f"💡 <b>Hint:</b>\n{hint}\n\nTap 📋 Solution if you need the full approach."

def handle_text_message(message_text, tracker):
    """Process user text message and route to appropriate handler"""
    intent = detect_intent(message_text)
    next_problem = get_next_problem(tracker)

    if not next_problem:
        return "🎉 All problems covered! Great work! Take a break and come back tomorrow. 🌟"

    logger.info(f"Text intent detected: {intent} | message: {message_text[:50]}")

    # 6 new Q&A use cases (specific intents)
    if intent == "pattern_explain":
        log_question(tracker, intent, message_text, next_problem["title"])
        msg = handle_pattern_explain(message_text, next_problem)
        idx = tracker["problems"].index(next_problem)
        # Return with follow-up buttons would need to be in poll_mode; for now just return msg
        return msg

    elif intent == "interview_prep":
        log_question(tracker, intent, message_text, next_problem["title"])
        return handle_interview_prep(next_problem)

    elif intent == "approach_check":
        log_question(tracker, intent, message_text, next_problem["title"])
        return handle_approach_check(next_problem)

    elif intent == "code_template":
        log_question(tracker, intent, message_text, next_problem["title"])
        return handle_code_template(next_problem)

    elif intent == "compare":
        log_question(tracker, intent, message_text, next_problem["title"])
        return handle_compare(message_text, next_problem)

    elif intent == "simplify":
        log_question(tracker, intent, message_text, next_problem["title"])
        return handle_problem_simplify(next_problem)

    # Original intents
    elif intent == "stuck":
        return handle_stuck_message(next_problem, tracker)

    elif intent == "solution":
        return generate_solution_preview(next_problem)

    elif intent == "stats":
        return get_learning_stats(tracker)

    elif intent == "weak":
        return analyze_weak_areas(tracker)

    elif intent == "plan":
        return f"""📋 <b>Suggested Study Plan</b>

Based on your progress:
1. 🌅 Morning: Learn the pattern (5 min)
2. ☀️ Afternoon: Solve the main problem (30 min)
3. 📖 Evening: Review any problems due today (20 min)
4. 🌙 Night: Review approach and similar patterns (5 min)

🔁 Repeat each problem every {tracker['metadata'].get('interval_days', 1)} days.

Remember: Consistency beats intensity. Daily practice wins! 💪"""

    elif intent == "done":
        return "🎉 <b>Awesome!</b> Mark your difficulty level with the buttons above to schedule the next review.\n\n✅ Easy | ⏸️ Medium | ❌ Hard"

    elif intent == "skip":
        next_p = get_next_problem(tracker)
        if next_p:
            msg = generate_afternoon_message(next_p)
            idx = tracker["problems"].index(next_p)
            return msg
        else:
            return "🎉 All problems covered!"

    elif intent == "difficulty":
        if "hard" in message_text.lower():
            return "📈 Noted! I'll make the next problem harder. Keep pushing your limits! 💪"
        elif "easy" in message_text.lower():
            return "✅ Noted! I'll adjust to more reasonable difficulty. Learning at your pace! 🎯"

    else:  # general question
        log_question(tracker, intent, message_text, next_problem["title"])
        client = Anthropic(api_key=CLAUDE_API_KEY)
        api_start = time.time()

        prompt = f"""User asked a question about DSA learning. Answer helpfully in 2-3 sentences.
Current problem: {next_problem['title']} ({next_problem['pattern']})
User question: {message_text}

Be encouraging and specific."""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )
            elapsed = (time.time() - api_start) * 1000
            logger.info(f"Claude API (Q&A): {elapsed:.0f}ms")
            return f"💭 <b>Answer:</b>\n\n{response.content[0].text}"
        except Exception as e:
            logger.error(f"Claude Q&A error: {e}")
            return "💡 That's a great question! Keep thinking deeply about it. 🧠\n\nTap a button above for quick actions."

OFFSET_FILE = SCRIPT_DIR / "telegram_offset.json"

def load_offset():
    if OFFSET_FILE.exists():
        with open(OFFSET_FILE) as f:
            return json.load(f).get("offset", 0)
    return 0

def save_offset(offset):
    with open(OFFSET_FILE, "w") as f:
        json.dump({"offset": offset}, f)

def poll_mode():
    """Fetch pending button taps and text messages from Telegram"""
    offset = load_offset()

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    api_start = time.time()
    response = requests.get(url, params={"offset": offset, "timeout": 0})
    elapsed_ms = (time.time() - api_start) * 1000

    if response.status_code != 200:
        logger.error(f"Telegram getUpdates failed: {response.status_code}")
        api_logger.log_call(
            service="telegram",
            method="GET",
            endpoint=url,
            request_obj={"headers": {}, "body": {"offset": offset, "timeout": 0}},
            response_obj={"status": response.status_code, "headers": dict(response.headers), "body": response.text},
            elapsed_ms=elapsed_ms
        )
        return

    updates = response.json().get("result", [])
    logger.info(f"Telegram getUpdates -> {response.status_code} OK | {len(updates)} update(s)")

    # Log API call
    api_logger.log_call(
        service="telegram",
        method="GET",
        endpoint=url,
        request_obj={"headers": {}, "body": {"offset": offset, "timeout": 0}},
        response_obj={"status": response.status_code, "headers": dict(response.headers), "body": {"updates_count": len(updates)}},
        elapsed_ms=elapsed_ms
    )

    if not updates:
        logger.debug("No new updates")
        return

    for update in updates:
        update_id = update["update_id"]

        # Handle text messages (new feature: direct chat input)
        if "message" in update:
            msg = update["message"]
            user_text = msg.get("text", "").strip()

            if user_text and not user_text.startswith("/"):  # Ignore commands
                logger.info(f"Text message received: {user_text[:50]}")
                tracker = load_tracker()

                response_msg = handle_text_message(user_text, tracker)
                send_telegram_message(response_msg)

                logger.info(f"Text message handled: {user_text[:30]}")

        elif "callback_query" in update:
            cq = update["callback_query"]
            callback_query_id = cq["id"]
            callback_data = cq.get("data", "")

            # Dismiss the loading spinner immediately
            answer_callback_query(callback_query_id)
            logger.debug(f"Callback: answered query {callback_query_id}")

            # Process the tap
            result = handle_button_callback(callback_data)

            if result:
                title, interval_days, action, extra = result

                if action == "hint":
                    problem = extra  # full problem dict
                    hint_msg = generate_hint_message(problem)
                    send_telegram_message(hint_msg)
                    logger.info(f"Hint sent for: {title}")

                elif action == "solution":
                    problem = extra  # full problem dict
                    solution_msg = generate_solution_preview(problem)
                    send_telegram_message(solution_msg)
                    logger.info(f"Solution sent for: {title}")

                elif action == "stuck":
                    problem = extra  # full problem dict
                    stuck_msg = handle_stuck_message(problem, load_tracker())
                    send_telegram_message(stuck_msg)
                    logger.info(f"Adaptive hint (stuck) sent for: {title}")

                elif action == "learn":
                    problem = extra  # full problem dict
                    pattern = problem["pattern"]
                    explanation = PATTERN_EXPLANATIONS.get(pattern, "Master this pattern for interview success.")
                    learn_msg = f"📚 <b>{pattern}</b>\n\n{explanation}\n\n💡 Ready to solve {problem['title']}?"
                    send_telegram_message(learn_msg)
                    logger.info(f"Pattern learning sent: {pattern}")

                elif action == "examples":
                    problem = extra  # full problem dict
                    pattern = problem["pattern"]
                    similar = [p for p in load_tracker()["problems"] if p["pattern"] == pattern and p["id"] != problem["id"]][:3]
                    similar_list = "\n".join([f"  • {p['title']} (LC #{p['leetcode_number']})" for p in similar]) if similar else "  No other examples yet"
                    examples_msg = f"📖 <b>More {pattern} Problems</b>\n\n{similar_list}\n\n🔗 Solve these to master the pattern!"
                    send_telegram_message(examples_msg)
                    logger.info(f"Examples sent for: {pattern}")

                elif action == "stats":
                    tracker_fresh = load_tracker()
                    stats_msg = get_learning_stats(tracker_fresh)
                    send_telegram_message(stats_msg)
                    logger.info(f"Learning stats sent")

                elif action == "weak":
                    tracker_fresh = load_tracker()
                    weak_msg = analyze_weak_areas(tracker_fresh)
                    send_telegram_message(weak_msg)
                    logger.info(f"Weak areas analysis sent")

                elif action == "plan":
                    plan_msg = """📋 <b>Suggested Study Plan</b>

Based on your progress:
1. 🌅 Morning: Learn the pattern (5 min)
2. ☀️ Afternoon: Solve the main problem (30 min)
3. 📖 Evening: Review any problems due today (20 min)
4. 🌙 Night: Review approach and similar patterns (5 min)

🔁 Repeat each problem every few days.

Remember: Consistency beats intensity. Daily practice wins! 💪"""
                    send_telegram_message(plan_msg)
                    logger.info(f"Study plan sent")

                elif action == "skip":
                    msg = f"⏭️ Skipped <b>{title}</b> — it'll come back tomorrow."
                    send_telegram_message(msg)

                elif action == "mastered":
                    msg = f"🏆 <b>Mastered!</b> <b>{title}</b> archived — it won't come back."
                    send_telegram_message(msg)
                    logger.info(f"Mastered: {title}")

                elif action == "solved":
                    msg = f"✅ <b>Awesome!</b> You solved <b>{title}</b>! Now rate the difficulty:\n\n✅ Easy | ⏸️ Medium | ❌ Hard"
                    send_telegram_message(msg)

                elif action == "toeasy":
                    msg = f"✅ Noted! <b>{title}</b> was too easy. I'll make the next problem more challenging. 📈"
                    send_telegram_message(msg)

                elif action == "tohard":
                    msg = f"❌ Noted! <b>{title}</b> was too hard. I'll adjust the difficulty. Let's build your confidence! 💪"
                    send_telegram_message(msg)

                elif action == "ready":
                    msg = f"💪 Great! Let's go solve <b>{title}</b>. You've got this! 🚀\n\nRemember: Solve it from first principles, don't just look at hints right away."
                    send_telegram_message(msg)

                # Follow-up actions from Q&A use cases
                elif action.startswith("followup_"):
                    sub_action = action.replace("followup_", "")
                    problem = extra  # full problem dict

                    if sub_action == "java":
                        msg = handle_code_template(problem)
                    elif sub_action == "interview":
                        msg = handle_interview_prep(problem)
                    elif sub_action == "similar":
                        pattern = problem["pattern"]
                        similar = [p for p in load_tracker()["problems"] if p["pattern"] == pattern and p["id"] != problem["id"]][:3]
                        similar_list = "\n".join([f"  • {p['title']} (LC #{p['leetcode_number']})" for p in similar]) if similar else "  No other examples yet"
                        msg = f"🔗 <b>Similar {pattern} Problems</b>\n\n{similar_list}"
                    elif sub_action == "solution":
                        msg = generate_solution_preview(problem)
                    elif sub_action == "complexity":
                        msg = handle_approach_check(problem)
                    elif sub_action == "hint":
                        msg = generate_hint_message(problem)
                    elif sub_action == "next":
                        tracker_fresh = load_tracker()
                        next_p = get_next_problem(tracker_fresh)
                        if next_p:
                            msg = generate_afternoon_message(next_p)
                            idx = tracker_fresh["problems"].index(next_p)
                            buttons = create_adaptive_buttons(idx, "afternoon")
                            send_telegram_message(msg, reply_markup=buttons)
                            logger.info(f"Next problem sent: {next_p['title']}")
                        else:
                            msg = "🎉 All problems covered! Come back tomorrow."
                    elif sub_action == "whentouse":
                        msg = f"💡 <b>When to Use Each:</b>\n\nCheck your notes and practice both approaches on similar problems!"
                    elif sub_action == "edgecases":
                        msg = f"📝 <b>Edge Cases to Consider:</b>\n\nThink about: empty input, single element, duplicates, large numbers, negative values."
                    elif sub_action == "stats":
                        tracker_fresh = load_tracker()
                        msg = get_learning_stats(tracker_fresh)
                    elif sub_action == "weak":
                        tracker_fresh = load_tracker()
                        msg = analyze_weak_areas(tracker_fresh)
                    elif sub_action == "plan":
                        msg = """📋 <b>Suggested Study Plan</b>

Based on your progress:
1. 🌅 Morning: Learn the pattern (5 min)
2. ☀️ Afternoon: Solve the main problem (30 min)
3. 📖 Evening: Review any problems due today (20 min)
4. 🌙 Night: Review approach and similar patterns (5 min)

🔁 Repeat each problem every few days.

Remember: Consistency beats intensity. Daily practice wins! 💪"""
                    elif sub_action == "askmore":
                        msg = "💬 <b>What would you like to know?</b>\n\nAsk me anything about this problem, the pattern, interview tips, or any DSA concept!"
                    else:
                        msg = "💬 Follow-up coming up!"

                    send_telegram_message(msg)
                    logger.info(f"Follow-up action {sub_action} sent for: {title}")

                elif action == "nextq":
                    tracker_fresh = load_tracker()
                    next_p = get_next_problem(tracker_fresh)
                    if next_p:
                        msg = generate_afternoon_message(next_p)
                        idx = tracker_fresh["problems"].index(next_p)
                        buttons = create_adaptive_buttons(idx, "afternoon")
                        send_telegram_message(msg, reply_markup=buttons)
                        logger.info(f"Next question sent: {next_p['title']}")
                    else:
                        send_telegram_message("🎉 All problems covered! Come back tomorrow.")

                elif action == "askq":
                    send_telegram_message(
                        "💬 <b>What would you like to know?</b>\n\n"
                        "Ask me anything about this problem, the pattern, interview tips, or any DSA concept!"
                    )
                    logger.info(f"Ask more prompt sent")

                else:
                    # difficulty rating: easy / medium / hard
                    emoji = {"easy": "✅", "medium": "⏸️", "hard": "❌"}.get(action, "📝")
                    msg = f"{emoji} Recorded as <b>{action.capitalize()}</b>!\n<b>{title}</b> → next review in <b>{interval_days} day(s)</b>"
                    send_telegram_message(msg)
                    logger.info(f"Callback processed: {action} for {title} | next_due={interval_days}d")

                    # Check pattern completion
                    tracker_fresh = load_tracker()
                    rated_problem = next((p for p in tracker_fresh["problems"] if p["title"] == title), None)
                    if rated_problem:
                        completed, total = check_pattern_completion(tracker_fresh, rated_problem)
                        if completed:
                            # Find next pattern
                            next_new = get_next_problem(tracker_fresh)
                            next_pattern = f" Up next: <b>{next_new['pattern']}</b>!" if next_new else ""
                            celebration = (
                                f"🎉 <b>Pattern Complete!</b>\n\n"
                                f"You've worked through all <b>{total}</b> problems in "
                                f"<b>{rated_problem['pattern']}</b>!{next_pattern}\n\n"
                                f"Keep the momentum going! 🚀"
                            )
                            send_telegram_message(celebration)
                            logger.info(f"Pattern complete: {rated_problem['pattern']}")

        save_offset(update_id + 1)
        logger.debug(f"Offset saved: {update_id + 1}")

    logger.info(f"Poll complete: {len(updates)} update(s) processed")

def main():
    parser = argparse.ArgumentParser(description="DSA SRS Telegram Reminder Bot")
    parser.add_argument("--mode", choices=["morning", "afternoon", "evening", "night", "poll"],
                       default="morning", help="Reminder mode to trigger")
    args = parser.parse_args()

    setup_logging(args.mode)

    try:
        # poll mode doesn't need Claude API key
        if args.mode != "poll" and not CLAUDE_API_KEY:
            logger.error("ANTHROPIC_API_KEY or CLAUDE_API_KEY environment variable not set")
            sys.exit(1)

        if args.mode == "morning":
            morning_mode()
        elif args.mode == "afternoon":
            afternoon_mode()
        elif args.mode == "evening":
            evening_mode()
        elif args.mode == "night":
            night_mode()
        elif args.mode == "poll":
            poll_mode()

        elapsed_ms = (time.time() - mode_start_time) * 1000
        logger.info(f"END | duration={elapsed_ms:.0f}ms")

    except Exception as e:
        elapsed_ms = (time.time() - mode_start_time) * 1000 if mode_start_time else 0
        logger.exception(f"Unhandled exception in {args.mode} mode after {elapsed_ms:.0f}ms")
        sys.exit(1)

if __name__ == "__main__":
    main()
