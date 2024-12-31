import random
from typing import Dict, Union, Optional

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
        if 0 <= level <= 12:  # Multiplication tables 0-12
            return generate_multiplication_problem(level)
    
    return None
