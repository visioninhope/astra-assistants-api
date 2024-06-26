import json
import asyncio
import subprocess
from datetime import datetime


from repro.agent_base import BaseAssistant


def initialise_agent():
    """
    Initializes the run session by setting up the necessary components.
    """
    agent_instructions = """
    You are Mirko, a skilled UX/UI Frontend Developer working on a Next.js 14 project with Shadcn UI components and Tailwind CSS for styling. Your focus is on creating a visually appealing and user-friendly interface using JavaScript and the Page Router.

    """

    agent_internal_monologue_system_message = f"""
    You are the internal monologue of Mirko – Self-reflect, critique and decide what to do next. Also make sure that we are not in a loop, sending the same messages back & forth – break the loop by using Gather_information_ask_user. 

    <MIRKO>
    {agent_instructions}
    </MIRKO>

    ALWAYS RESPOND IN THE FOLLOWING JSON FORMAT:
    {{
        "observations": " ",
        "thoughts": " ",
        "next_actions": " ",
    }}
    """

    agent = BaseAssistant("Mirko.ai", agent_instructions)
    
    working_memory_content = json.dumps({}, indent=3)
    current_datetime = datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
    additional_instructions = f"Working Memory <WorkingMemory> {working_memory_content} </WorkingMemory>\nCurrent Date and Time: {current_datetime}"

    return (agent_instructions, agent_internal_monologue_system_message,
            agent, additional_instructions)



async def start_session_run(user_request):
    (agent_instructions, agent_internal_monologue_system_message,
     agent, additional_instructions) = initialise_agent()

    try:
        subprocess.run(["tmux", "kill-server"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to kill tmux server: {e}")

    thread_id = agent.start_new_thread()

    # agent.generate_playground_access(thread_id)

    while True:
        run_id = agent.run_thread(thread_id, agent.assistant_id, additional_instructions=additional_instructions)

        await agent.check_run_status_and_execute_action(thread_id, run_id)

        agent.internal_monologue(thread_id, agent_internal_monologue_system_message)

if __name__ == "__main__":
    user_request = """ 
    Build a Website for my construction business
    """        
    asyncio.run(start_session_run(user_request))
