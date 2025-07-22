#!/usr/bin/env python3
"""
Autonomous SRE Self-Healing Bot - Main Execution Script
Runs the complete self-healing workflow for incident detection and automated resolution
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
            logging.FileHandler("logs/self_heal_main.log"),
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
        logging.error("Please set the following environment variables:")
        for var in missing_vars:
            logging.error(f"  export {var}='your_token_here'")
        return False
    
    # Optional but recommended
    if not os.getenv('KUBECONFIG'):
        logging.warning("KUBECONFIG not set, will use default ~/.kube/config")
    
    return True

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Autonomous SRE Self-Healing Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default settings
  python main_self_heal.py
  
  # Run with specific namespace and priority
  python main_self_heal.py --namespace staging --priority Critical
  
  # Run with custom incident keywords
  python main_self_heal.py --keywords "OutOfMemory,PodRestartThreshold,ImagePullBackOff"
  
  # Run in dry-run mode (analysis only, no fixes)
  python main_self_heal.py --dry-run
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
        '--keywords',
        help='Comma-separated incident keywords to filter (e.g., "OutOfMemory,CrashLoop")'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Analyze incidents but do not create fixes or PRs'
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
        '--output-file',
        help='File to save workflow results (JSON format)'
    )
    
    return parser.parse_args()

def main():
    """Main execution function"""
    # Parse arguments
    args = parse_arguments()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("Autonomous SRE Self-Healing Bot Starting")
    logger.info("=" * 60)
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    try:
        # Create the self-healing crew
        logger.info("Initializing self-healing crew...")
        crew = create_self_healing_crew(config_path=args.config_path)
        
        # Show crew status
        status = crew.get_crew_status()
        logger.info(f"Crew initialized successfully: {status}")
        
        # Prepare workflow inputs
        workflow_inputs = {
            "timestamp": datetime.now().isoformat(),
            "namespace": args.namespace,
            "priority_threshold": args.priority,
            "dry_run": args.dry_run,
            "workflow_type": "autonomous_self_healing"
        }
        
        # Add incident keywords if provided
        if args.keywords:
            workflow_inputs["incident_keywords"] = [
                keyword.strip() for keyword in args.keywords.split(',')
            ]
        else:
            workflow_inputs["incident_keywords"] = [
                "OutOfMemory", "CrashLoopBackOff", "PodRestartThreshold",
                "ImagePullBackOff", "FailedMount", "Unhealthy"
            ]
        
        logger.info(f"Workflow inputs: {json.dumps(workflow_inputs, indent=2)}")
        
        if args.dry_run:
            logger.info("Running in DRY-RUN mode - no fixes will be applied")
        
        # Execute the self-healing workflow
        logger.info("Starting self-healing workflow execution...")
        result = crew.execute_self_healing_workflow(workflow_inputs)
        
        # Log results
        if result.get('success'):
            logger.info("Self-healing workflow completed successfully!")
        else:
            logger.error(f"Self-healing workflow failed: {result.get('error')}")
        
        # Save results to file if requested
        if args.output_file:
            output_path = Path(args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            
            logger.info(f"Results saved to: {output_path}")
        
        # Print summary
        logger.info("=" * 60)
        logger.info("Execution Summary:")
        logger.info(f"  Success: {result.get('success', False)}")
        logger.info(f"  Timestamp: {result.get('timestamp', 'N/A')}")
        logger.info(f"  Namespace: {args.namespace}")
        logger.info(f"  Priority: {args.priority}")
        logger.info(f"  Dry Run: {args.dry_run}")
        
        if not result.get('success'):
            logger.info(f"  Error: {result.get('error', 'Unknown error')}")
        
        logger.info("=" * 60)
        
        # Exit with appropriate code
        sys.exit(0 if result.get('success') else 1)
        
    except KeyboardInterrupt:
        logger.info("Execution interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
