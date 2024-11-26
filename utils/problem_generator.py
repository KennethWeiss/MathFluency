import random

def generate_addition_problem(level):
    """Generate addition problems based on level
    Level 1: Adding 1 to single digit
    Level 2: Adding 2 to single digit
    Level 3: Making sums equal to 10
    Level 4: Single digit to double digit
    Level 5: Double digit to double digit
    """
    if level == 1:  # Adding 1 to single digit
        num = random.randint(0, 9)
        return f"{num} + 1", num + 1
        
    elif level == 2:  # Adding 2 to single digit
        num = random.randint(0, 9)
        return f"{num} + 2", num + 2
        
    elif level == 3:  # Making sums equal to 10
        num = random.randint(1, 9)
        return f"{num} + ____ = 10", 10 - num
        
    elif level == 4:  # Single digit to double digit
        num1 = random.randint(10, 99)
        num2 = random.randint(1, 9)
        return f"{num1} + {num2}", num1 + num2
        
    elif level == 5:  # Double digit to double digit
        num1 = random.randint(10, 99)
        num2 = random.randint(10, 99)
        return f"{num1} + {num2}", num1 + num2
    
    raise ValueError("Invalid level")

def generate_multiplication_problem(level):
    """Generate multiplication problems for a specific number
    Levels are the numbers 0-12 to practice
    Recommended progression: 0,1 → 2 → 5 → 10 → 11 → 3 → 4 → 6 → 8 → 7
    """
    if level not in range(13):
        raise ValueError("Invalid level")
        
    num = random.randint(0, 12)
    return f"{num} × {level}", num * level

def get_problem(operation, level):
    """Main function to get problems based on operation and level"""
    if operation == 'addition':
        return generate_addition_problem(level)
    elif operation == 'multiplication':
        return generate_multiplication_problem(level)
    else:
        raise ValueError("Invalid operation")