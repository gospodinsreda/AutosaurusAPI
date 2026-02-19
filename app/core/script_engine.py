"""Script Engine for executing JSON-based automation scripts"""
import logging
import time
import re
from typing import Any, Dict, List, Optional
from app.models.script import Script, ScriptStep
from app.models.action import ActionRequest, ActionType
from app.core.action_executor import ActionExecutor
from app.core.session_manager import SessionManager

logger = logging.getLogger(__name__)


class ScriptEngine:
    """
    Engine for parsing and executing JSON-based automation scripts.
    
    Features:
    - Variable interpolation ($variable_name)
    - Control flow (if/then/else, loops)
    - Error handling strategies (skip, retry, abort)
    - Action execution via ActionExecutor
    - Execution tracking and metrics
    """
    
    def __init__(
        self,
        session_manager: SessionManager,
        session_id: str,
        variables: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize ScriptEngine.
        
        Args:
            session_manager: Session manager instance
            session_id: ID of the browser session
            variables: Initial variables for the script
        """
        self.session_manager = session_manager
        self.session_id = session_id
        self.variables = variables or {}
        self.steps_completed = 0
        self.start_time = 0.0
        
        # Get session and create action executor
        session = self.session_manager.get_session(session_id)
        if not session:
            raise RuntimeError(f"Session not found: {session_id}")
        
        driver = session["engine"].driver
        self.action_executor = ActionExecutor(driver, self.variables)
    
    def interpolate_value(self, value: Any) -> Any:
        """
        Replace variable placeholders with actual values.
        
        Args:
            value: Value that may contain $variable_name placeholders
            
        Returns:
            Value with variables replaced
        """
        if not isinstance(value, str):
            return value
        
        result = value
        for var_name, var_value in self.variables.items():
            placeholder = f"${var_name}"
            if placeholder in result:
                result = result.replace(placeholder, str(var_value))
        
        return result
    
    def evaluate_condition(self, condition: Dict[str, Any]) -> bool:
        """
        Evaluate a condition for if/then/else control flow.
        
        Args:
            condition: Condition dict with variable, operator, and value
            
        Returns:
            bool: Result of condition evaluation
        """
        variable_name = condition.get("variable")
        operator = condition.get("operator")
        expected_value = condition.get("value")
        
        if not variable_name or not operator:
            logger.warning("Invalid condition: missing variable or operator")
            return False
        
        # Get actual variable value
        actual_value = self.variables.get(variable_name)
        
        # Interpolate expected value
        expected_value = self.interpolate_value(expected_value)
        
        # Evaluate based on operator
        if operator == "equals":
            return str(actual_value) == str(expected_value)
        elif operator == "not_equals":
            return str(actual_value) != str(expected_value)
        elif operator == "contains":
            return str(expected_value) in str(actual_value)
        elif operator == "not_contains":
            return str(expected_value) not in str(actual_value)
        elif operator == "greater_than":
            try:
                return float(actual_value) > float(expected_value)
            except (ValueError, TypeError):
                return False
        elif operator == "less_than":
            try:
                return float(actual_value) < float(expected_value)
            except (ValueError, TypeError):
                return False
        elif operator == "greater_equal":
            try:
                return float(actual_value) >= float(expected_value)
            except (ValueError, TypeError):
                return False
        elif operator == "less_equal":
            try:
                return float(actual_value) <= float(expected_value)
            except (ValueError, TypeError):
                return False
        elif operator == "exists":
            return actual_value is not None
        elif operator == "not_exists":
            return actual_value is None
        elif operator == "is_empty":
            return not actual_value or len(str(actual_value)) == 0
        elif operator == "not_empty":
            return actual_value and len(str(actual_value)) > 0
        else:
            logger.warning(f"Unknown operator: {operator}")
            return False
    
    def execute_step(self, step: ScriptStep, retry_count: int = 0) -> Any:
        """
        Execute a single script step.
        
        Args:
            step: ScriptStep to execute
            retry_count: Current retry attempt number
            
        Returns:
            Result of the step execution
            
        Raises:
            Exception: If step execution fails and error strategy is 'abort'
        """
        try:
            # Handle control flow - conditionals
            if step.condition and step.then_steps:
                condition_result = self.evaluate_condition(step.condition)
                logger.info(f"Condition evaluated to: {condition_result}")
                
                if condition_result and step.then_steps:
                    for then_step in step.then_steps:
                        self.execute_step(then_step)
                elif not condition_result and step.else_steps:
                    for else_step in step.else_steps:
                        self.execute_step(else_step)
                
                self.steps_completed += 1
                return None
            
            # Handle control flow - loops
            if step.loop_range and step.loop_steps:
                if len(step.loop_range) != 2:
                    raise ValueError("loop_range must have exactly 2 elements: [start, end]")
                
                start, end = step.loop_range
                loop_var = step.loop_variable or "i"
                
                logger.info(f"Starting loop from {start} to {end} with variable {loop_var}")
                
                for i in range(start, end + 1):
                    # Set loop variable
                    self.variables[loop_var] = i
                    self.action_executor.variables[loop_var] = i
                    
                    # Execute loop steps
                    for loop_step in step.loop_steps:
                        self.execute_step(loop_step)
                
                self.steps_completed += 1
                return None
            
            # Regular action execution
            action_request = self._step_to_action(step)
            result = self.action_executor.execute(action_request)
            
            # Save result to variable if requested
            if step.save_as:
                self.variables[step.save_as] = result
                self.action_executor.variables[step.save_as] = result
                logger.info(f"Saved result to variable: {step.save_as} = {result}")
            
            self.steps_completed += 1
            return result
            
        except Exception as e:
            logger.error(f"Error executing step: {e}")
            
            # Handle error based on strategy
            error_strategy = step.on_error or "abort"
            max_retry = step.max_retry or 3
            
            if error_strategy == "skip":
                logger.warning(f"Skipping failed step: {e}")
                self.steps_completed += 1
                return None
            
            elif error_strategy == "retry" and retry_count < max_retry:
                logger.info(f"Retrying step (attempt {retry_count + 1}/{max_retry})")
                time.sleep(1)  # Brief delay before retry
                return self.execute_step(step, retry_count + 1)
            
            elif error_strategy == "abort":
                logger.error(f"Aborting script execution: {e}")
                raise
            
            else:
                # Max retries exceeded
                logger.error(f"Max retries exceeded for step: {e}")
                raise
    
    def _step_to_action(self, step: ScriptStep) -> ActionRequest:
        """
        Convert a ScriptStep to an ActionRequest.
        
        Args:
            step: ScriptStep to convert
            
        Returns:
            ActionRequest for execution
        """
        # Interpolate step values
        return ActionRequest(
            action=ActionType(step.action),
            selector=self.interpolate_value(step.selector) if step.selector else None,
            url=self.interpolate_value(step.url) if step.url else None,
            text=self.interpolate_value(step.text) if step.text else None,
            value=self.interpolate_value(step.value) if step.value else None,
            script=self.interpolate_value(step.script) if step.script else None,
        )
    
    def execute_script(self, script: Script) -> Dict[str, Any]:
        """
        Execute a complete script.
        
        Args:
            script: Script to execute
            
        Returns:
            Dict with execution results including:
                - success: bool
                - execution_time: float
                - steps_completed: int
                - variables: Dict[str, Any]
                - error: Optional[str]
        """
        logger.info(f"Starting script execution: {script.name}")
        self.start_time = time.time()
        self.steps_completed = 0
        
        # Merge script variables with existing variables
        if script.variables:
            self.variables.update(script.variables)
            self.action_executor.variables.update(script.variables)
        
        error_message = None
        
        try:
            # Execute each step
            for step in script.steps:
                self.execute_step(step)
            
            success = True
            logger.info(f"Script completed successfully: {script.name}")
            
        except Exception as e:
            success = False
            error_message = str(e)
            logger.error(f"Script execution failed: {e}")
        
        execution_time = time.time() - self.start_time
        
        return {
            "success": success,
            "execution_time": execution_time,
            "steps_completed": self.steps_completed,
            "variables": self.variables.copy(),
            "error": error_message
        }
