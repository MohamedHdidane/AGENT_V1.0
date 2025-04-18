import logging
import os
import json
import traceback

import mythic_container
from igidir import IgidirAgent  # registers the payload type
from mythic_container import mythic_service


def start_agent_service():
    """
    Start the Mythic agent service for the Igidir agent.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - [%(levelname)s] - %(message)s",
    )

    try:
        # Optional: Load config if needed
        config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "rabbitmq_config.json")
        if os.path.exists(config_file):
            with open(config_file, 'r') as config_json:
                config = json.load(config_json)
                logging.info("RabbitMQ config loaded successfully.")

        # ✅ THIS is now just a regular call, no asyncio.run!
        mythic_service.start_and_run_forever()

    except Exception as e:
        logging.error(f"Failed to start agent service: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    start_agent_service()
