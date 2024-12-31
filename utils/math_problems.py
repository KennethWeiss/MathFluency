import random
from typing import Dict, Union, Optional, Tuple, List

# Type hint for a problem
Problem = Dict[str, Union[str, int, float]]

def generate_addition_level1() -> Problem:
    """Adding 1 to single digit"""
    num = random.randint(1, 9)
    return {
        'problem': f"{num} + 1",
        'answer': num + 1,
        'description': "Adding 1 to single digit",
        'operation': 'addition',
        'level': 1
    }

def generate_addition_level2() -> Problem:
    """Adding 2 to single digit"""
    num = random.randint(1, 9)
    return {
        'problem': f"{num} + 2",
        'answer': num + 2,
        'description': "Adding 2 to single digit",
        'operation': 'addition',
        'level': 2
    }

def generate_addition_level3() -> Problem:
    """Make 10 problems"""
    num1 = random.randint(1, 9)
    num2 = 10 - num1  # This makes the sum equal to 10
    return {
        'problem': f"{num1} + {num2}",
        'answer': 10,
        'description': "Make 10",
        'operation': 'addition',
        'level': 3
    }

def generate_addition_level4() -> Problem:
    """Add single digit to double digit"""
    num1 = random.randint(10, 99)  # Double digit
    num2 = random.randint(1, 9)    # Single digit
    return {
        'problem': f"{num1} + {num2}",
        'answer': num1 + num2,
        'description': "Add single digit to double digit",
        'operation': 'addition',
        'level': 4
    }

def generate_addition_level5() -> Problem:
    """Add double digit to double digit"""
    num1 = random.randint(10, 99)
    num2 = random.randint(10, 99)
    return {
        'problem': f"{num1} + {num2}",
        'answer': num1 + num2,
        'description': "Add double digit to double digit",
        'operation': 'addition',
        'level': 5
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
    if operation == 'addition':
        if level == 1:
            return generate_addition_level1()
        elif level == 2:
            return generate_addition_level2()
        elif level == 3:
            return generate_addition_level3()
        elif level == 4:
            return generate_addition_level4()
        elif level == 5:
            return generate_addition_level5()
    elif operation == 'multiplication':
        if level == 99:  # Special level for custom problems
            number1_spec = {'type': 'range', 'value': (2, 6)}
            number2_spec = {'type': 'set', 'value': [2, 7, 8]}
            return generate_custom_multiplication(number1_spec, number2_spec)
        elif 0 <= level <= 12:  # Regular multiplication tables 0-12
            return generate_multiplication_problem(level)
    
    return None  # Invalid operation or level
