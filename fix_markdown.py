import requests
import json
import os
import argparse
import time
import subprocess


def prepend_filename_with_fixed(file_path):
    # Split the file path into directory and filename
    directory, filename = os.path.split(file_path)

    # Split the filename into name and extension
    name, extension = os.path.splitext(filename)

    # Create the new filename by appending '_fixed' before the extension
    new_filename = f"{name}_fixed{extension}"

    # Join the directory and new filename to create the new path
    new_file_path = os.path.join(directory, new_filename)

    return new_file_path


def process_markdown_file(file_path, args):
    # Function to process a single markdown file
    with open(file_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    separator = "\n------SEPARATOR------\n"
    task = f"""Your task is to:

    1. Identify and correct any grammatical errors.
    2. Check for and fix any broken links.
    3. Address any formatting issues.
    4. Do not modify anchors within headers.
    5. Provide a brief explanation of the changes made.
    6. If no changes are necessary, respond with "The page reads great, no changes required."
    7. If any change is required your response should include
        1. The revised content of the markdown file.
        2. An explanation of your changes, after adding this separator {separator}.

    Here is an example response:
    # Logging Into Polaris

    To log into Polaris:
    ```bash
    ssh <username>@polaris.alcf.anl.gov
    ```
    Then, type in the password from your CRYPTOCard/MobilePASS+ token.

    ------SEPARATOR------

    1. Fixed grammar: replaced pasword with password.
    2. Improved formatting: added bash syntax highlighting for readability."""

    prompt = f"Please review the following markdown file for errors and improvements: {md_content} \n---\n {task}"

    data = {
        "user": args.user,
        "model": args.model,
        "system": "You are an AI language model designed to assist with reviewing and improving markdown documentation for ALCF supercomputers. Your task is to identify and correct any errors in grammar, broken links, and formatting issues within the provided markdown files. You should also provide a brief explanation of the changes made. Ensure that the revised markdown maintains clarity and accuracy, and adheres to best practices for technical documentation.",
        "prompt": [prompt],
        "stop": [],
        "temperature": args.temperature,
        "top_p": args.top_p,
        "max_tokens": args.max_tokens,
        "max_completion_tokens": args.max_completion_tokens,
    }

    # Convert the dict to JSON
    payload = json.dumps(data)

    # Add a header stating that the content type is JSON
    headers = {"Content-Type": "application/json"}

    start_time = time.time()

    # Send POST request
    response = requests.post(args.url, data=payload, headers=headers)

    end_time = time.time()  # End timing
    response_time = end_time - start_time
    print(f"Response Time: {response_time:.2f} seconds")

    # Receive the response data
    print("Status Code: ", response.status_code)

    res = response.json().get("response", "")
    res_parts = res.split(separator)
    if len(res_parts) == 2:
        fixed_md = res_parts[0].strip()
        # Write the markdown content to the original file or a new file
        if args.inplace:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(fixed_md)
            print(f"Markdown file modified in place at: {file_path}")
        else:
            fixed_md_file = prepend_filename_with_fixed(file_path)
            with open(fixed_md_file, "w", encoding="utf-8") as f:
                f.write(fixed_md)
            print(f"Fixed markdown file written at: {fixed_md_file}")
        explanation = res_parts[1].strip()
        print(f"Explanation:\n{explanation}")

        if args.commit:
            subprocess.run(["git", "add", file_path], check=True)
            subprocess.run(["git", "commit", "-m", explanation], check=True)
            print("Changes committed to Git.")
    else:
        print("*" * 25)
        print(f" Problem detected, please check response:\n{res}")
        print("*" * 25)


def main(args):
    if os.path.isdir(args.md_path):
        # If the path is a directory, search for markdown files recursively
        for root, _, files in os.walk(args.md_path):
            for file in files:
                if file.endswith(".md"):  # Check for markdown files
                    file_path = os.path.join(root, file)
                    process_markdown_file(file_path, args)
    else:
        # Process a single markdown file
        process_markdown_file(args.md_path, args)


if __name__ == "__main__":
    # Argument parser setup
    parser = argparse.ArgumentParser(
        description="Process markdown file for grammar and formatting improvements."
    )
    parser.add_argument("md_path", help="Path to the markdown file.")
    parser.add_argument(
        "--url",
        default="REPLACE WITH ARGO URL",
        help="API endpoint URL.",
    )
    parser.add_argument("--user", default="keceli", help="User for the API request.")
    parser.add_argument(
        "--model", default="gpt4o", help="Model to use (e.g., gpt4o, gpt35)."
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="Sampling temperature for the model.",
    )
    parser.add_argument(
        "--top_p", type=float, default=0.9, help="Top-p sampling for the model."
    )
    parser.add_argument(
        "--max_tokens", type=int, default=10000, help="Max tokens for the prompt."
    )
    parser.add_argument(
        "--max_completion_tokens",
        type=int,
        default=10000,
        help="Max tokens for the completion.",
    )
    parser.add_argument(
        "--inplace",
        action="store_true",
        help="Modify the original markdown file instead of creating a new one."
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Commit changes to Git with the explanation as the commit message."
    )

    # Parse arguments
    args = parser.parse_args()

    # Run main function with parsed arguments
    main(args)
