import logging
import os
import sys
import traceback
from mythic_container import mythic_service
import mythic_container
import json

# Import our agent-specific components
from igidir import IgidirAgent


async def start_agent_service():
    """
    Start the Mythic agent service for the Igidir agent
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - [%(levelname)s] - %(message)s",
    )
    
    try:
        # Load config from rabbitmq_config.json
        config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rabbitmq_config.json")
        with open(config_file, 'r') as config_json:
            config = json.load(config_json)
        
        # Create our agent service
        agent_service = mythic_service.PayloadServiceRPC(
            payload_type="igidir",
            service_name="igidir_payload_service",
            rabbit_host=config["rabbit_host"],
            rabbit_port=config["rabbit_port"],
            rabbit_vhost=config["rabbit_vhost"],
        )

        # Register our agent with the service
        igidir_agent = IgidirAgent()
        await agent_service.register_payload_type_service(igidir_agent)
        
        # Start listening for tasking
        await agent_service.start()
        
    except Exception as e:
        logging.error(f"Failed to start agent service: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    # Start the async event loop for the agent service
    mythic_container.run_asyncio(start_agent_service())