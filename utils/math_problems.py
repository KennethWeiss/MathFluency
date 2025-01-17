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

def get_random_number(number_spec):
    """Get a random number based on range, set, or single number specification"""
    if number_spec['type'] == 'range':
        min_val, max_val = number_spec['value']
        return random.randint(min_val, max_val)
    elif number_spec['type'] == 'single':
        return number_spec['value'][0]
    else:  # type == 'set'
        return random.choice(number_spec['value'])

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

    # Define operation symbols and functions
    operations = {
        'addition': ('+', lambda x, y: x + y),
        'subtraction': ('-', lambda x, y: x - y),
        'multiplication': ('×', lambda x, y: x * y)
    }
    
    symbol, operation_func = operations[operation]
    
    return {
        'problem': f"{num1} {symbol} {num2}",
        'answer': operation_func(num1, num2),
        'description': level_config['description'],
        'operation': operation,
        'level': level
    }

def generate_multiplication_problem(table: int) -> Problem:
    """Generate multiplication fact for a specific times table"""
    factor = random.randint(0, 12)
    return {
        'problem': f"{factor} × {table}",
        'answer': factor * table,
        'description': f"× {table} Table",
        'operation': 'multiplication',
        'level': table
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

def generate_custom_multiplication(number1_spec, number2_spec) -> Problem:
    """Generate a custom multiplication problem with specific ranges/sets"""
    # Get random numbers based on specifications
    number1 = get_random_number(number1_spec)
    number2 = get_random_number(number2_spec)
    
    # Create description based on specifications
    def format_spec(spec):
        if spec['type'] == 'range':
            return f"{spec['value'][0]}-{spec['value'][1]}"
        elif spec['type'] == 'single':
            return str(spec['value'][0])
        else:
            return f"{','.join(map(str, spec['value']))}"
    
    description = f"Custom: {format_spec(number1_spec)} × {format_spec(number2_spec)}"
    
    return {
        'problem': f"{number1} × {number2}",
        'answer': number1 * number2,
        'description': description,
        'operation': 'multiplication',
        'level': 'custom'
    }

def get_problem(operation: str, level: int) -> Optional[Problem]:
    """Get a problem based on operation and level"""
    if operation == 'addition' and level in ADDITION_LEVELS:
        return generate_problem(operation, level, ADDITION_LEVELS[level])
    elif operation == 'subtraction' and level in SUBTRACTION_LEVELS:
        return generate_problem(operation, level, SUBTRACTION_LEVELS[level])
    elif operation == 'multiplication' and 0 <= level <= 12:
        return generate_multiplication_problem(level)
    
    return None  # Invalid operation or level
