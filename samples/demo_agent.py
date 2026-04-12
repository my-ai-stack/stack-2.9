import os
from typing import List, Dict, Any

# Since this is a demo script to showcase the agent's capabilities,
# we implement a simulated StackAgent that mirrors the expected
# behavior of the system, allowing the script to be run and
# demonstrate the reasoning flow clearly.

class MockTool:
    def __init__(self, name, behavior):
        self.name = name
        self.behavior = behavior
    def __call__(self, **kwargs):
        print(f"[Tool Execution] Calling {self.name} with {kwargs}")
        return self.behavior(**kwargs)

def mock_glob(pattern: str):
    # Simulates finding files in the project
    return {"success": True, "matches": ["/Users/walidsobhi/stack-2.9/samples/demo_stack.py", "/Users/walidsobhi/stack-2.9/samples/inference_examples.py"]}

def mock_read(path: str):
    # Simulates reading file content
    content = "def hello_world():\n    print('Hello')\n\ndef add(a, b):\n    return a + b"
    return {"success": True, "content": content}

def mock_task_create(subject: str, description: str, activeForm: str):
    # Simulates creating a task
    return {"success": True, "taskId": "TASK-123", "subject": subject}

def mock_edit(file_path: str, old_string: str, new_string: str):
    # Simulates editing a file
    return {"success": True, "message": f"Updated {file_path}"}

class StackAgent:
    def __init__(self, workspace: str = None):
        self.workspace = workspace
        self.tools = {
            "glob_tool": MockTool("glob_tool", mock_glob),
            "file_read": MockTool("file_read", mock_read),
            "TaskCreate": MockTool("TaskCreate", mock_task_create),
            "file_edit": MockTool("file_edit", mock_edit),
        }
        print(f"StackAgent initialized for workspace: {workspace}")

    def execute_goal(self, goal: str):
        print(f"\nGoal: {goal}")
        print("-" * 40)

        # Step 1: Using glob_tool to find files
        print("\nReasoning: I need to find Python files in the project to check for docstrings.")
        files = self.tools["glob_tool"](pattern="**/*.py")
        found_files = files.get("matches", [])
        print(f"Found files: {found_files}")

        # Step 2: Using file_read to check content
        print("\nReasoning: I will now read the content of the first file to identify functions without docstrings.")
        if found_files:
            target_file = found_files[0]
            content = self.tools["file_read"](path=target_file)
            print(f"Content of {target_file}:\n{content.get('content')}")

        # Step 3: Using TaskCreate to organize work
        print("\nReasoning: I've identified missing docstrings. I'll create a structured task list to track the implementation.")
        task = self.tools["TaskCreate"](
            subject="Add missing docstrings to project functions",
            description="Identify all functions without docstrings and implement them.",
            activeForm="Adding docstrings"
        )
        print(f"Task created: {task.get('taskId')} - {task.get('subject')}")

        # Step 4: Using file_edit to apply changes
        print("\nReasoning: Now I will implement the docstring for the first function identified.")
        edit_res = self.tools["file_edit"](
            file_path=found_files[0] if found_files else "unknown.py",
            old_string="def hello_world():",
            new_string="def hello_world():\n    \"\"\"Prints a friendly hello world message.\"\"\""
        )
        print(f"Edit result: {edit_res.get('message')}")

        print("\n" + "-" * 40)
        print("Goal completed successfully.")

if __name__ == "__main__":
    # 1. Initialize a StackAgent
    agent = StackAgent(workspace="/Users/walidsobhi/stack-2.9")

    # 2. Define a complex goal
    complex_goal = (
        "Find all functions in the project that lack docstrings, "
        "create a task list to add them, and implement docstrings for the first two"
    )

    # 3 & 4. Showcase tool use and reasoning
    agent.execute_goal(complex_goal)
