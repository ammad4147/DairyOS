import os
import ollama

# --- 1. DEFINE PROJECT TOOLS ---

def read_file(file_path: str, **kwargs) -> str:
    """Read and return the contents of a local file inside the project.
    Args:
        file_path: Relative path to the file (e.g., 'main.py' or 'models/db.py')
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

def write_file(file_path: str, content: str, **kwargs) -> str:
    """Write or overwrite content to a local file inside the project.
    Args:
        file_path: Relative path to the file
        content: The text content to write
    """
    try:
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

def list_directory(path=".", depth=None, **kwargs) -> str:
    """List all files and folders in the project directory."""
    try:
        items = []
        target_path = path if path else "."
        for root, dirs, files in os.walk(target_path):
            if ".venv" in root or ".git" in root or "__pycache__" in root:
                continue
            for file in files:
                items.append(os.path.join(root, file))
        return "\n".join(items)
    except Exception as e:
        return f"Error listing directory: {str(e)}"

available_tools = {
    'read_file': read_file,
    'write_file': write_file,
    'list_directory': list_directory,
}

# --- 2. RUN AGENT LOOP WITH GPT-OSS:20B ---

def run_dairy_agent(user_prompt):
    model_name = "gpt-oss:20b"
    
    messages = [
        {
            "role": "system",
            "content": "You are an autonomous AI software assistant working inside the DairyOS project directory. "
                       "You have tools to list files, read files, and write files. "
                       "Inspect the workspace when necessary and call tools to read/write files to completely fulfill the user request."
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]

    print(f"🐮 DairyOS Agent (`{model_name}`) Initialized.\nPrompt: '{user_prompt}'\n" + "-"*50)

    while True:
        response = ollama.chat(
            model=model_name,
            messages=messages,
            tools=[read_file, write_file, list_directory]
        )

        messages.append(response.message)

        if response.message.tool_calls:
            for tool in response.message.tool_calls:
                func_name = tool.function.name
                func_args = tool.function.arguments
                
                print(f"🛠️  AI Tool Call: `{func_name}`")
                print(f"    Arguments: {func_args}")

                if func_name in available_tools:
                    tool_output = available_tools[func_name](**func_args)
                    print(f"📄 Output Snippet: {str(tool_output)[:200]}...\n")

                    messages.append({
                        'role': 'tool',
                        'tool_name': func_name,
                        'content': str(tool_output)
                    })
                else:
                    print(f"❌ Tool {func_name} not found.\n")
        else:
            print("-" * 50)
            print("✨ Agent Task Complete:\n")
            print(response.message.content)
            break

if __name__ == "__main__":
    import sys
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "List the project files and analyze the workspace structure."
    run_dairy_agent(prompt)