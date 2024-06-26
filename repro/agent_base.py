from typing import List, Dict
import json
import inspect
import asyncio
import logging

import dotenv

# =========================
# Initiations
# =========================
dotenv.load_dotenv()

from openai import OpenAI
from astra_assistants import patch
client = patch(OpenAI())


# =========================
# Base Assistant Class
# =========================

class BaseAssistant:
    def __init__(self, name: str, instructions: str, tools: List[Dict] = []):
        self.name = name
        self.instructions = instructions
        self.tools = tools
        self.assistant_id = self.create_assistant(name, instructions, tools)

    @staticmethod
    def create_assistant(name, instructions, tools=[], model="anthropic/claude-3-5-sonnet-20240620"):
        
        assistant = client.beta.assistants.create(
            name=name,
            instructions=instructions,
            tools=tools,
            model=model,
            temperature=0.1
        )
        return assistant.id

    @staticmethod
    def start_new_thread():
        empty_thread = client.beta.threads.create()
        return empty_thread.id

    @staticmethod
    def add_message(thread_id, content, role="user"):
        thread_message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role=role,
            content=content,
        )
        return thread_message
    
    def run_thread(self, thread_id, assistant_id, additional_instructions):
            return self.run_thread_helper(thread_id, assistant_id, additional_instructions)

    @staticmethod
    def run_thread_helper(thread_id, assistant_id, additional_instructions):
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            additional_instructions=additional_instructions
        )
        return run.id


    @staticmethod
    def get_run(thread_id, run_id):
        run = client.beta.threads.runs.retrieve(
        thread_id=thread_id,
        run_id=run_id
        )
        return run

    @staticmethod
    def get_messages_in_thread(thread_id, stringified=False):
        messages = client.beta.threads.messages.list(thread_id)
        # Sort messages by 'created_at' to ensure they are in the correct order
        sorted_messages = sorted(messages.data, key=lambda x: x.created_at)
        if stringified:
            string_messages = []
            for message in sorted_messages:
                role = "Internal Monologue" if message.role.lower() == "user" else message.role.upper()
                # Assuming the first item in content list is the main text
                content = message.content[0].text.value
                string_messages.append(f"{role}: {content}")
            return "\n\n".join(string_messages)
        return sorted_messages

    async def check_run_status_and_execute_action(self, thread_id: str, run_id: str):
        while True:
            run = self.get_run(thread_id, run_id)
            if run.status == "requires_action":
                await self.execute_run_action(run_id, thread_id)
                await asyncio.sleep(3)
            elif run.status in ["in_progress", "queued", "cancelling"]:
                await asyncio.sleep(3)                
            elif run.status in ["completed", "cancelled", "failed", "expired"]:
                break

    async def execute_run_action(self, run_id, thread_id):
        run = BaseAssistant.get_run(thread_id, run_id)
        required_action = run.required_action if run.status == "requires_action" else None
        logging.info(f"Debug: Required action for run_id {run_id} is {required_action}")

        if required_action and required_action.type == "submit_tool_outputs":
            tool_calls = required_action.submit_tool_outputs.tool_calls
            tool_outputs = []
            logging.info(f"Debug: Processing {len(tool_calls)} tool calls for submission.")

            for tool_call in tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                logging.info(f"Debug: Attempting to execute function {function_name} with arguments {arguments}")

                # Dynamically call the function with the provided arguments
                try:
                    # Attempt to find the function in any tool instance
                    function = None
                    for tool_instance in []:
                        if hasattr(tool_instance, function_name):
                            function = getattr(tool_instance, function_name)
                            logging.info(f"Debug: Found function {function_name} in {type(tool_instance).__name__}")
                            break

                    if function:
                        # Execute the function asynchronously if it's a coroutine
                        if inspect.iscoroutinefunction(function):
                            output = await function(**arguments)
                        else:
                            output = function(**arguments)
                        logging.info(f"Debug: Function {function_name} executed successfully with output: {output}")
                        if isinstance(output):
                            output = output.output
                    else:
                        output = "Function not found"
                        logging.info(f"Debug: Function {function_name} not found in any tool instance")
                except Exception as e:
                    output = f"An exception has occurred: {e}"
                    logging.info(f"Debug: Exception occurred while executing function {function_name}: {e}")

                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": str(output)  # Convert output to string to avoid type error
                })

            # Submit the tool outputs
            try:
                run = client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run_id,
                    tool_outputs=tool_outputs
                )
                logging.info(f"Debug: Successfully submitted tool outputs for run_id {run_id}")
            except Exception as e:
                logging.info(f"Failed to submit tool outputs for run_id {run_id}: {e}")
    
    
    def internal_monologue(self, thread_id, monologue_system_message):
        messages_in_thread = self.get_messages_in_thread(thread_id, stringified=True)
        # Include working memory in the user message

        working_memory_content = json.dumps({}, indent=3)
        
        messages = [
            {
                "role": "system",
                "content": f"{monologue_system_message}"
            },
            {
                "role": "user",
                "content": f"<ConversationHistory> {messages_in_thread} </ConversationHistory> \n <WorkingMemory> {working_memory_content} </WorkingMemory>"
            },
        ]
        #response = make_llm_api_call(messages, model_name="anthropic/claude-3-5-sonnet-20240620", json_mode=True)
        new_message_contents = "puppies"
        self.add_message(thread_id, new_message_contents, role="user")
        return new_message_contents


    def generate_playground_access(self, thread_id):
        playground_url = f'https://platform.openai.com/playground?assistant={self.assistant_id}&mode=assistant&thread={thread_id}'
        logging.info(f'Playground Access URL: {playground_url}')
