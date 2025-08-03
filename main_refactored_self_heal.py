#!/usr/bin/env python3
"""
Refactored Autonomous SRE Self-Healing Bot - Main Execution Script
Runs the agent-driven self-healing workflow where agents fetch and manage incidents
"""

import os
import sys
import argparse
import logging
import json
from datetime import datetime
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from autonomous_sre_bot.self_heal_crew import create_self_healing_crew

def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)
    
    # Setup file and console logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler("logs/refactored_self_heal_main.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def validate_environment():
    """Validate required environment variables"""
    required_vars = [
        'GITHUB_TOKEN',
        'ATLASSIAN_TOKEN', 
        'ATLASSIAN_CLOUD_ID'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logging.error(f"Missing required environment variables: {missing_vars}")
        logging.error("Please set these variables before running the self-healing bot")
        return False
    
    # Optional but recommended variables
    optional_vars = [
        'GITHUB_OWNER',
        'GITHUB_REPO',
        'OPENAI_API_KEY'
    ]
    
    missing_optional = []
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
    
    if missing_optional:
        logging.warning(f"Missing optional environment variables: {missing_optional}")
        logging.warning("Some functionality may be limited")
    
    return True

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Refactored Autonomous SRE Self-Healing Bot")
    parser.add_argument(
        "--log-level", 
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help="Set the logging level"
    )
    parser.add_argument(
        "--assignee", 
        default="manoharnv",
        help="Filter incidents by assignee (default: autonomous-sre)"
    )
    parser.add_argument(
        "--priority", 
        default="High,Critical",
        help="Filter incidents by priority (comma-separated, default: High,Critical)"
    )
    parser.add_argument(
        "--max-incidents", 
        type=int,
        default=5,
        help="Maximum number of incidents to process (default: 5)"
    )
    parser.add_argument(
        "--config-path",
        default="src/autonomous_sre_bot/config",
        help="Path to configuration files"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in simulation mode without making actual changes"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    logger.info("=" * 80)  
    logger.info("REFACTORED AUTONOMOUS SRE SELF-HEALING BOT STARTUP")
    logger.info("=" * 80)
    logger.info(f"Log Level: {args.log_level}")
    logger.info(f"Assignee Filter: {args.assignee}")
    logger.info(f"Priority Filter: {args.priority}")
    logger.info(f"Max Incidents: {args.max_incidents}")
    logger.info(f"Config Path: {args.config_path}")
    logger.info(f"Dry Run: {args.dry_run}")

    # Validate environment
    if not validate_environment():
        logger.error("Environment validation failed. Exiting.")
        sys.exit(1)

    try:
        # Create and configure the refactored self-healing crew
        logger.info("Initializing refactored self-healing crew...")
        crew = create_self_healing_crew(
            config_path=args.config_path,
            log_level=args.log_level
        )
        logger.info("Refactored crew initialized successfully")

        # Prepare workflow inputs
        workflow_inputs = {
            "timestamp": datetime.now().isoformat(),
            "workflow_type": "refactored_autonomous_self_healing",
            "assignee_filter": args.assignee,
            "priority_filter": args.priority,
            "max_incidents": args.max_incidents,
            "dry_run": args.dry_run,
            "config_path": args.config_path
        }

        logger.info("Starting refactored self-healing workflow...")
        logger.info(f"Workflow inputs: {json.dumps(workflow_inputs, indent=2)}")

        # Execute the workflow
        start_time = datetime.now()
        result = crew.execute_self_healing_workflow(workflow_inputs)
        end_time = datetime.now()
        
        execution_time = (end_time - start_time).total_seconds()
        
        # Log results
        logger.info("=" * 80)
        logger.info("REFACTORED WORKFLOW EXECUTION COMPLETED")
        logger.info("=" * 80)
        logger.info(f"Execution Time: {execution_time:.2f} seconds")
        logger.info(f"Success: {result.get('success', False)}")
        
        if result.get('success'):
            logger.info("Workflow completed successfully!")
            logger.info("Result summary:")
            logger.info(f"  - Workflow Type: {result.get('inputs', {}).get('workflow_type', 'Unknown')}")
            logger.info(f"  - Timestamp: {result.get('timestamp', 'Unknown')}")
            logger.info(f"  - Message: {result.get('message', 'No message')}")
        else:
            logger.error("Workflow failed!")
            logger.error(f"Error: {result.get('error', 'Unknown error')}")
            logger.error(f"Message: {result.get('message', 'No message')}")

        # Save results to file
        results_file = f"logs/refactored_self_heal_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump({
                **result,
                "execution_time_seconds": execution_time,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "command_line_args": vars(args)
            }, f, indent=2)
        
        logger.info(f"Results saved to: {results_file}")

        # Exit with appropriate code
        if result.get('success'):
            logger.info("Refactored self-healing bot completed successfully")
            sys.exit(0)
        else:
            logger.error("Refactored self-healing bot failed")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.warning("Execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error during execution: {str(e)}")
        logger.exception("Full traceback:")
        sys.exit(1)

if __name__ == "__main__":
    main()
