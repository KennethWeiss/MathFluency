import random
from typing import Dict, Union, Optional, Tuple, List

# Type hint for a problem
Problem = Dict[str, Union[str, int, float]]

# Define level configurations for each operation
ADDITION_LEVELS = {
    1: {
        'description': "Adding 1 to single digit",
        'num1': {'type': 'range', 'value': (1, 9)},
        'num2': {'type': 'single', 'value': [1]}
    },
    2: {
        'description': "Adding 2 to single digit",
        'num1': {'type': 'range', 'value': (1, 9)},
        'num2': {'type': 'single', 'value': [2]}
    },
    3: {
        'description': "Make 10",
        'custom_generator': lambda: (random.randint(1, 9), lambda x: 10 - x)
    },
    4: {
        'description': "Add single digit to double digit",
        'num1': {'type': 'range', 'value': (10, 99)},
        'num2': {'type': 'range', 'value': (1, 9)}
    },
    5: {
        'description': "Add double digit to double digit",
        'num1': {'type': 'range', 'value': (10, 99)},
        'num2': {'type': 'range', 'value': (10, 99)}
    }
}

SUBTRACTION_LEVELS = {
    1: {
        'description': "Subtracting 1 from single digit",
        'num1': {'type': 'range', 'value': (2, 10)},
        'num2': {'type': 'single', 'value': [1]}
    },
    2: {
        'description': "Subtracting 2 from single digit",
        'num1': {'type': 'range', 'value': (3, 10)},
        'num2': {'type': 'single', 'value': [2]}
    },
    3: {
        'description': "Subtract from 10",
        'num1': {'type': 'single', 'value': [10]},
        'num2': {'type': 'range', 'value': (1, 9)}
    },
    4: {
        'description': "Subtract single digit from double digit",
        'num1': {'type': 'range', 'value': (11, 99)},
        'num2': {'type': 'range', 'value': (1, 9)}
    },
    5: {
        'description': "Subtract double digit from double digit",
        'num1': {'type': 'range', 'value': (11, 99)},
        'custom_generator': lambda num1: (num1, lambda x: random.randint(1, x-1))
    }
}

MULTIPLICATION_LEVELS = {
    'standard': {  # Standard multiplication tables 0-12
        1: {
            'description': "×1 Table",
            'num1': {'type': 'single', 'value': [1]},
            'num2': {'type': 'range', 'value': (0, 12)}
        },
        2: {
            'description': "×2 Table",
            'num1': {'type': 'single', 'value': [2]},
            'num2': {'type': 'range', 'value': (0, 12)}
        },
        # ... more standard levels
    },
    'custom': {  # For teacher-defined multiplication
        'description': "Custom multiplication",
        'parse_input': True,  # Flag to indicate this needs input parsing
    }
}

def get_random_number(number_spec):
    """Get a random number based on range, set, or single number specification"""
    if number_spec['type'] == 'range':
        min_val, max_val = number_spec['value']
        return random.randint(min_val, max_val)
    elif number_spec['type'] == 'single':
        return number_spec['value'][0]  # Return the single number
    else:  # type == 'set'
        return random.choice(number_spec['value'])

def parse_number_input(input_str: str) -> List[int]:
    """Parse a string containing comma-separated numbers or a range.
    
    Args:
        input_str: String like "2,3,5" or "1-10"
    Returns:
        List of integers
    """
    if not input_str or not isinstance(input_str, str):
        return []
        
    input_str = input_str.strip()
    if '-' in input_str:
        try:
            start, end = map(int, input_str.split('-'))
            return list(range(start, end + 1))
        except (ValueError, TypeError):
            return []
    elif ',' in input_str:
        try:
            return [int(x.strip()) for x in input_str.split(',') if x.strip()]
        except (ValueError, TypeError):
            return []
    else:
        try:
            return [int(input_str)]
        except (ValueError, TypeError):
            return []

def generate_multiplication_questions(multiplicands: str, num_questions: int = 10) -> List[Problem]:
    """Generate a set of multiplication problems using the given multiplicands.
    
    Args:
        multiplicands: String containing numbers (e.g., "2,3,5" or "1-10")
        num_questions: Number of questions to generate
    Returns:
        List of Problem dictionaries with 'problem' and 'answer' keys
    """
    numbers = parse_number_input(multiplicands)
    if not numbers:
        return []
    
    # Create a custom level configuration
    custom_level = {
        'num1': {'type': 'set', 'value': numbers},
        'num2': {'type': 'range', 'value': (0, 12)}
    }
    
    questions = []
    for _ in range(num_questions):
        problem = generate_problem('multiplication', 'custom', custom_level)
        questions.append(problem)
    
    return questions

def generate_problem(operation: str, level: int, level_config: dict) -> Problem:
    """Generate a problem based on operation and level configuration"""
    if 'custom_generator' in level_config:
        if callable(level_config['custom_generator']):
            # For simple custom generators (like Make 10)
            num1, num2_func = level_config['custom_generator']()
            num2 = num2_func(num1) if callable(num2_func) else num2_func
        else:
            # For more complex custom generators
            num1 = get_random_number(level_config['num1'])
            num2_func = level_config['custom_generator'](num1)
            num2 = num2_func(num1) if callable(num2_func) else num2_func
    else:
        num1 = get_random_number(level_config['num1'])
        num2 = get_random_number(level_config['num2'])

    # Define operation symbols
    symbols = {
        'addition': '+',
        'subtraction': '-',
        'multiplication': '×'
    }
    
    # Define operation functions
    operations = {
        'addition': lambda x, y: x + y,
        'subtraction': lambda x, y: x - y,
        'multiplication': lambda x, y: x * y
    }
    
    return {
        'problem': f"{num1} {symbols[operation]} {num2}",
        'answer': operations[operation](num1, num2),
        'description': level_config['description'],
        'operation': operation,
        'level': level
    }

def get_problem(operation: str, level: int) -> Optional[Problem]:
    """Get a problem based on operation and level"""
    if operation == 'addition' and level in ADDITION_LEVELS:
        return generate_problem(operation, level, ADDITION_LEVELS[level])
    elif operation == 'subtraction' and level in SUBTRACTION_LEVELS:
        return generate_problem(operation, level, SUBTRACTION_LEVELS[level])
    elif operation == 'multiplication':
        if level == 'custom':
            return None  # Custom levels need multiplicand input
        elif level in MULTIPLICATION_LEVELS['standard']:
            return generate_problem(operation, level, MULTIPLICATION_LEVELS['standard'][level])
    
    return None  # Invalid operation or level
