# Import standard packages
import asyncio
import json
from typing import Any

# Import langchain packages
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

# Import custom packages
from src.beri import Beri
from src.beri.models import SplitPolicy
from src.llm.config import LLM_BASE_URL, MODEL_ID
from src.llm.models import NVerdict, NPlan, ToolCall, NState
from src.llm.utils import load_system_prompt

class N_A_M_I:
    """
    Shared expense / Splitwise specialist agent that uses Beri tools.
    """
    
    # WHat does NAMI need?
    # A planner agent to understand all the tools it has and decide which tools to use
    # An executor agent to execute the tool calls decided by the planner agent
    # A state graph going from planner -> executor
    
    def __init__(self):
        """
        Initialize some state variables for the NAMI workflow.
        """
        self.beri = Beri()
        self.system_prompt = load_system_prompt("NAMI/N-A-M-I.md") or ""
        self.planner_instructions = load_system_prompt("NAMI/Planner.md") or ""
        self.executor_instructions = load_system_prompt("NAMI/Executor.md") or ""
        
        # Initialize the LLM for both planner and executor
        # Langchain takes ollama models as "<model>" instead of "ollama/<model>"
        self.llm = ChatOllama(
            model=MODEL_ID,
            base_url=LLM_BASE_URL,
            temperature=0.2,
        )
        
        # Instantiate the planner and executor w/ their respective output classes
        self.planner = self.llm.with_structured_output(NPlan)
        self.executor = self.llm.with_structured_output(NVerdict)
        
        # Create the state graph
        self._workflow = self.create_workflow()
        
        return
    
    def plan(self, state: NState) -> dict[str, Any]:
        """
        Planner node for the NAMI workflow.
        
        Args:
            state (str): The input state
        
        Returns:
            dict[str, Any]: The dictionary to update in the graph's global state
        """
        # Call the planner to draft the plan of execution
        plan: NPlan = self.planner.invoke(
            [
                SystemMessage(content=self.system_prompt),
                SystemMessage(content=self.planner_instructions),
                HumanMessage(content=state.input),
            ]
        )

        return {"plan": plan}
    
    def execute(self, state: NState) -> dict[str, Any]:
        """
        Executor node for the NAMI workflow.
        
        Args:
            state (NPlan): The input state for the executor. Usually will be the plan from the planner.
        
        Returns:
            dict[str, Any]: The dictionary to update in the graph's global state (hopefully w/ text and gif_search_query)
        """
        plan = state.plan
        
        # Instantiate and construct all tool results from the planning phase
        tool_results: list[dict[str, Any]] = []
        serialized_tool_calls: list[dict[str, Any]] = []
        
        for raw_call in (plan.tool_calls or []):
            try:
                call = ToolCall.model_validate(raw_call)
                serialized_tool_calls.append(call.model_dump())
                result = self._dispatch_tool_call(call)
                tool_results.append(
                    {
                        "name": call.name,
                        "args": call.args,
                        "result": result
                    }
                )
                
            except Exception as e:
                # Ensure that all tool call exceptions are propagated to the agent
                tool_results.append(
                    {
                        "call": raw_call,
                        "error": str(e)
                    }
                )

        # Call the executor for final summarization
        verdict: NVerdict = self.executor.invoke(
            [
                SystemMessage(content=self.system_prompt),
                SystemMessage(content=self.executor_instructions),
                HumanMessage(
                    content=json.dumps(
                        {
                            "input": state.input,
                            "plan": plan.plan if plan else "",
                            "tool_calls": serialized_tool_calls,
                            "tool_results": tool_results,
                        },
                        ensure_ascii=False,
                    )
                ),
            ]
        )

        return {"verdict": verdict}
    
    def create_workflow(self) -> CompiledStateGraph:
        """
        Routine responsible for creating the LangGraph state graph w/ the planner and executor agents.
        
        Architecture:
        - The NAMI agent follows a planner -> executor design
        - The planner decides which Beri tool calls to make (if any), with args
        - The executor is responsible for running the tool calls provided by the planner and return a validated `NVerdict` JSON response
        """
        # Initialize the graph (no nodes yet)
        graph = StateGraph(NState)

        # Add the planner and executor nodes
        graph.add_node("planner", self.plan)
        graph.add_node("executor", self.execute)

        # Define the flow
        # For now the flow does not introduce any loops and exits after 1 pass through
        graph.add_edge(START, "planner")
        graph.add_edge("planner", "executor")
        graph.add_edge("executor", END)
        
        # TODO: Conditional Chaining
        # workflow.add_conditional_edges(
        #     "executor",
        #     lambda state: "planner" if state["revision_needed"] else END
        # )

        # Compile the graph
        workflow = graph.compile()
        
        return workflow

    def run(self, input: str) -> NVerdict:
        """
        Run the agent workflow.
        """
        # Execute the workflow
        result = self._workflow.invoke({"input": input})
        
        # Validate the presence of a final verdict
        verdict = result.get("verdict")
        if not verdict:
            raise ValueError("NAMI failed to generate a verdict!")
        
        return NVerdict.model_validate(verdict)

    def _dispatch_tool_call(self, tool: ToolCall) -> Any:
        """
        Subroutine to execute the tool calls listed by the executor agent.

        Args:
            call (ToolCall): The tool call to execute

        Returns:
            Any: The outputs of the tool call
        """
        # Match and execute the decided tool name
        match tool.name:
            # Execute Beri's get_friends routine
            case "get_friends":
                return self.beri.get_friends()
            
            # Execute Beri's get_groups routine
            case "get_groups":
                return self.beri.get_groups()
            
            # Execute Beri's log_expense routine
            case "log_expense":
                # Extract all arguments
                args = dict(tool.args or {})
                
                # Extract the patron and recipient
                # TODO: Move the recipients (w/ patron logic) in system prompt
                patron = str(args["patron"])
                recipients = list(set([str(name) for name in list(args["recipients"]) + [patron]]))

                # Instantiate the split policy
                split_policy = args.get("split_policy") or "EQUAL"
                try:
                    split_policy = SplitPolicy[split_policy]
                except Exception:
                    raise ValueError("split_policy must be one of: EQUAL, AMOUNTS, PERCENTAGE")

                # Finally, call Beri's log_expense routine
                return self.beri.log_expense(
                    amount=float(args["amount"]),
                    description=str(args["description"]),
                    patron=patron,
                    recipients=recipients,
                    recipient_shares=dict(args.get("recipient_shares") or {}),
                    split_policy=split_policy,
                    group_name=args.get("group_name"),
                )
        
        return
        
async def main():
    """
    Main function to run and test the N.A.M.I. agent.
    """
    
    # Initialize the NAMI agent
    agent = N_A_M_I()
    print("--- N.A.M.I. Interactive CLI (LangChain planner/executor) ---")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            # Get user input from the terminal
            user_input = input("You: ")
            
            # Ensure to have an exit case
            if user_input.lower() in ["exit", "quit"]:
                break
            
            if not user_input.strip():
                continue
            
            # Hit up NAMI
            verdict = agent.run(user_input)
            
            print(f"\nN.A.M.I.: {verdict.text}")
        
        except KeyboardInterrupt:
            break
    
    return

if __name__ == "__main__":
    asyncio.run(main())
