#!/usr/bin/env python3
"""
Autonomous SRE Self-Healing Daemon
Continuously monitors JSM for actionable incidents and processes them using state-driven workflow
"""

import os
import sys
import time
import signal
import argparse
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from autonomous_sre_bot.self_heal_crew import create_self_healing_crew
from autonomous_sre_bot.logging_config import setup_logging
from autonomous_sre_bot.tools.jira_mcp_tools import get_support_team_jira_tools

class SelfHealingDaemon:
    """
    Daemon that continuously monitors and processes incidents using JSM state management
    """
    
    def __init__(self, config_path: str = "src/autonomous_sre_bot/config", 
                 poll_interval: int = 300, log_level: str = "INFO"):  # 5 minutes default
        self.config_path = config_path
        self.poll_interval = poll_interval
        self.log_level = log_level
        self.running = False
        
        # Setup logging first
        setup_logging(log_level)
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.crew = create_self_healing_crew(config_path, log_level)
        # Using direct JIRA MCP tools through the crew now instead of separate state manager
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def start(self, namespace: str = "production", priority: str = "High"):
        """
        Start the daemon
        
        Args:
            namespace: Kubernetes namespace to monitor
            priority: Minimum incident priority to process
        """
        self.logger.info("=" * 60)
        self.logger.info("Autonomous SRE Self-Healing Daemon Starting")
        self.logger.info("=" * 60)
        self.logger.info(f"Configuration:")
        self.logger.info(f"  Namespace: {namespace}")
        self.logger.info(f"  Priority: {priority}")
        self.logger.info(f"  Poll Interval: {self.poll_interval} seconds")
        self.logger.info(f"  Config Path: {self.config_path}")
        
        self.running = True
        
        workflow_inputs = {
            "namespace": namespace,
            "priority_threshold": priority,
            "daemon_mode": True
        }
        
        iteration = 0
        
        try:
            while self.running:
                iteration += 1
                self.logger.info(f"--- Daemon Iteration {iteration} ---")
                
                try:
                    # Execute one cycle of the state-driven workflow
                    result = self.crew.execute_self_healing_workflow(workflow_inputs)
                    
                    # Log results
                    if result.get('success'):
                        incidents_processed = result.get('incidents_processed', 0)
                        self.logger.info(f"Cycle {iteration}: Processed {incidents_processed} incidents")
                        
                        if incidents_processed > 0:
                            # Log details of processed incidents
                            for incident_info in result.get('processed_incidents', []):
                                incident_key = incident_info.get('incident_key')
                                state = incident_info.get('current_state')
                                step_success = incident_info.get('step_result', {}).get('success', False)
                                self.logger.info(f"  {incident_key}: {state} -> {'Success' if step_success else 'Failed'}")
                    else:
                        self.logger.error(f"Cycle {iteration} failed: {result.get('error')}")
                
                except Exception as e:
                    self.logger.error(f"Error in daemon cycle {iteration}: {e}", exc_info=True)
                
                # Sleep until next poll interval
                if self.running:
                    self.logger.info(f"Sleeping for {self.poll_interval} seconds...")
                    time.sleep(self.poll_interval)
        
        except KeyboardInterrupt:
            self.logger.info("Daemon interrupted by user")
        
        finally:
            self.logger.info("Autonomous SRE Self-Healing Daemon Stopped")
    
    def get_status(self) -> dict:
        """Get current daemon status"""
        return {
            "running": self.running,
            "poll_interval": self.poll_interval,
            "config_path": self.config_path,
            "crew_status": self.crew.get_crew_status()
        }

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
        print(f"ERROR: Missing required environment variables: {missing_vars}")
        print("Please set the following environment variables:")
        for var in missing_vars:
            print(f"  export {var}='your_token_here'")
        return False
    
    return True

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Autonomous SRE Self-Healing Daemon",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run daemon with default settings (5 min polling)
  python daemon_self_heal.py
  
  # Run with custom polling interval (1 minute)
  python daemon_self_heal.py --poll-interval 60
  
  # Run for specific namespace and priority
  python daemon_self_heal.py --namespace staging --priority Critical
  
  # Run with debug logging
  python daemon_self_heal.py --log-level DEBUG
        """
    )
    
    parser.add_argument(
        '--namespace',
        default='production',
        help='Kubernetes namespace to monitor (default: production)'
    )
    
    parser.add_argument(
        '--priority',
        choices=['Low', 'Medium', 'High', 'Critical'],
        default='High',
        help='Minimum incident priority to process (default: High)'
    )
    
    parser.add_argument(
        '--poll-interval',
        type=int,
        default=300,
        help='Polling interval in seconds (default: 300 = 5 minutes)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--config-path',
        default='src/autonomous_sre_bot/config',
        help='Path to configuration files (default: src/autonomous_sre_bot/config)'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show daemon status and exit'
    )
    
    return parser.parse_args()

def main():
    """Main daemon execution"""
    args = parse_arguments()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    if not validate_environment():
        sys.exit(1)
    
    try:
        # Create daemon
        daemon = SelfHealingDaemon(
            config_path=args.config_path,
            poll_interval=args.poll_interval,
            log_level=args.log_level
        )
        
        if args.status:
            # Just show status and exit
            status = daemon.get_status()
            print(json.dumps(status, indent=2))
            sys.exit(0)
        
        # Start the daemon
        daemon.start(
            namespace=args.namespace,
            priority=args.priority
        )
        
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
