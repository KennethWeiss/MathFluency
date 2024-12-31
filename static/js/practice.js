let currentOperation = 'addition';
let problemStartTime = null;
let currentProblem = null;
let wrongAttempts = 0;

const VALIDATION_RULES = {
    MAX_SET_SIZE: 10,         // Maximum numbers in a set
    MIN_NUMBER: 0,            // Minimum allowed number
    MAX_NUMBER: 100,          // Maximum allowed number
    MAX_RANGE_SPAN: 20,       // Maximum difference between min and max in a range
};

function validateNumber(num) {
    // Check if it's a valid integer within allowed range
    return !isNaN(num) && 
           Number.isInteger(num) && 
           num >= VALIDATION_RULES.MIN_NUMBER && 
           num <= VALIDATION_RULES.MAX_NUMBER;
}

function validateRange(min, max) {
    // Check if range is valid and within limits
    if (!validateNumber(min) || !validateNumber(max)) {
        return { valid: false, error: "Numbers must be between 0 and 100" };
    }
    if (min > max) {
        return { valid: false, error: "First number must be less than or equal to second number" };
    }
    if (max - min > VALIDATION_RULES.MAX_RANGE_SPAN) {
        return { valid: false, error: `Range span cannot exceed ${VALIDATION_RULES.MAX_RANGE_SPAN}` };
    }
    return { valid: true };
}

function validateSet(numbers) {
    // Check if set is valid and within limits
    if (numbers.length === 0) {
        return { valid: false, error: "At least one number is required" };
    }
    if (numbers.length > VALIDATION_RULES.MAX_SET_SIZE) {
        return { valid: false, error: `Cannot have more than ${VALIDATION_RULES.MAX_SET_SIZE} numbers` };
    }
    const invalidNumbers = numbers.filter(n => !validateNumber(n));
    if (invalidNumbers.length > 0) {
        return { valid: false, error: "All numbers must be between 0 and 100" };
    }
    // Check for duplicates
    if (new Set(numbers).size !== numbers.length) {
        return { valid: false, error: "Duplicate numbers are not allowed" };
    }
    return { valid: true };
}

function parseNumberInput(input) {
    input = input.trim();
    
    // Handle empty input
    if (!input) {
        return { valid: false, error: "Input is required" };
    }
    
    // Handle single number
    if (!input.includes('-') && !input.includes(',')) {
        const num = parseInt(input);
        if (validateNumber(num)) {
            return { valid: true, data: { type: 'single', value: [num] } };
        }
        return { valid: false, error: "Invalid number format" };
    }
    
    // Handle range format (e.g., "2-7")
    if (input.includes('-')) {
        // Check if there's exactly one hyphen
        if (input.split('-').length !== 2) {
            return { valid: false, error: "Invalid range format. Use exactly one '-' (e.g., 2-7)" };
        }
        
        const [min, max] = input.split('-').map(n => parseInt(n.trim()));
        const rangeValidation = validateRange(min, max);
        if (!rangeValidation.valid) {
            return rangeValidation;
        }
        return { valid: true, data: { type: 'range', value: [min, max] } };
    }
    
    // Handle set format (e.g., "2,4,6")
    if (input.includes(',')) {
        const numbers = input.split(',')
            .map(n => parseInt(n.trim()))
            .filter(n => !isNaN(n));
            
        const setValidation = validateSet(numbers);
        if (!setValidation.valid) {
            return setValidation;
        }
        return { valid: true, data: { type: 'set', value: numbers } };
    }
    
    return { valid: false, error: "Invalid input format" };
}

function formatErrorMessage(input1, input2) {
    let messages = [];
    
    if (!input1.trim() || !input2.trim()) {
        messages.push("Both number fields are required");
        return messages.join('<br>');
    }
    
    const result1 = parseNumberInput(input1);
    const result2 = parseNumberInput(input2);
    
    if (!result1.valid) {
        messages.push(`First number: ${result1.error}`);
    }
    if (!result2.valid) {
        messages.push(`Second number: ${result2.error}`);
    }
    
    return messages.join('<br>');
}

async function getNewProblem() {
    const level = currentOperation === 'addition' 
        ? document.getElementById('addition-select').value 
        : document.getElementById('multiplication-select').value;
    
    try {
        let requestData = {
            operation: currentOperation,
            level: parseInt(level)
        };

        // Add custom range/set data if using custom multiplication
        if (currentOperation === 'multiplication' && level === '99') {
            const num1Input = document.getElementById('num1-input').value;
            const num2Input = document.getElementById('num2-input').value;
            
            const num1Result = parseNumberInput(num1Input);
            const num2Result = parseNumberInput(num2Input);

            if (!num1Result.valid || !num2Result.valid) {
                document.getElementById('feedback').innerHTML = 
                    `<div class="alert alert-danger">${formatErrorMessage(num1Input, num2Input)}</div>`;
                return;
            }

            requestData.customNumbers = {
                number1: num1Result.data,
                number2: num2Result.data
            };
        }

        const response = await fetch('/get_problem', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const problemData = await response.json();
        if (problemData.error) {
            throw new Error(problemData.error);
        }
        
        displayProblem(problemData);
        document.getElementById('correct-answer-hidden').value = problemData.answer;
        document.getElementById('answer-input').value = '';
        document.getElementById('feedback').innerHTML = '';
        document.getElementById('answer-input').focus();
        wrongAttempts = 0;
        problemStartTime = Date.now();
        
    } catch (error) {
        console.error('Error getting new problem:', error);
        document.getElementById('feedback').innerHTML = 
            `<div class="alert alert-danger">Error getting new problem: ${error.message}</div>`;
    }
}

function displayProblem(data) {
    if (data.all_mastered) {
        // Create congratulations message
        const problemDiv = document.getElementById('current-problem');
        problemDiv.innerHTML = `
            <div class="alert alert-success">
                <h4 class="alert-heading">Congratulations! 🎉</h4>
                <p>You've mastered all problems in Level ${data.level} ${data.operation}!</p>
                ${data.next_level ? `
                    <hr>
                    <p class="mb-0">Ready for a new challenge? Try Level ${data.next_level}!</p>
                    <button class="btn btn-primary mt-3" onclick="moveToNextLevel('${data.operation}', ${data.next_level})">
                        Move to Level ${data.next_level}
                    </button>
                ` : `
                    <hr>
                    <p class="mb-0">You've reached the highest level! Keep practicing to maintain your skills.</p>
                `}
            </div>
        `;
        
        // Hide answer input and check button
        document.getElementById('answer-section').style.display = 'none';
        document.getElementById('answer-hint').style.display = 'none';
        return;
    }

    // Show answer input and check button for normal problems
    document.getElementById('answer-section').style.display = 'block';
    document.getElementById('current-problem').textContent = data.problem;
    currentProblem = data;
    
    if (data.show_answer) {
        document.getElementById('correct-answer').textContent = data.answer;
        document.getElementById('answer-hint').style.display = 'block';
    } else {
        document.getElementById('answer-hint').style.display = 'none';
    }
}

function moveToNextLevel(operation, level) {
    // Update the level select
    const select = document.getElementById(`${operation}-select`);
    select.value = level;
    
    // Get a new problem at the new level
    getNewProblem();
}

// Operation selection
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('[data-operation]').forEach(button => {
        button.addEventListener('click', function() {
            const operation = this.getAttribute('data-operation');
            currentOperation = operation;
            
            // Update UI
            document.querySelectorAll('[data-operation]').forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            
            // Show/hide appropriate level select
            document.getElementById('addition-select').style.display = operation === 'addition' ? 'block' : 'none';
            document.getElementById('multiplication-select').style.display = operation === 'multiplication' ? 'block' : 'none';
            
            // Show/hide custom range/settings when multiplication level changes
            document.getElementById('multiplication-select').addEventListener('change', function() {
                const customSettings = document.getElementById('custom-range-settings');
                customSettings.style.display = this.value === '99' ? 'block' : 'none';
            });

            getNewProblem();
        });
    });

    // New problem button
    document.getElementById('new-problem').addEventListener('click', getNewProblem);

    // Add event listeners for selection menus
    document.getElementById('addition-select').addEventListener('change', getNewProblem);
    document.getElementById('multiplication-select').addEventListener('change', getNewProblem);


    // Check answer
    document.getElementById('check-answer').addEventListener('click', function() {
        const userAnswer = document.getElementById('answer-input').value;
        const correctAnswer = document.getElementById('correct-answer-hidden').value;
        const timeTaken = (Date.now() - problemStartTime) / 1000;  // Convert to seconds
        
        // Check answer on frontend
        const isCorrect = parseInt(userAnswer) === parseInt(correctAnswer);
        const feedback = document.getElementById('feedback');
        
        // Record attempt
        fetch('/record_attempt', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                operation: currentOperation,
                level: currentOperation === 'addition' 
                    ? document.getElementById('addition-select').value 
                    : document.getElementById('multiplication-select').value,
                problem: document.getElementById('current-problem').textContent,
                userAnswer: parseInt(userAnswer),
                correctAnswer: parseInt(correctAnswer),
                isCorrect: isCorrect,
                timeTaken: timeTaken
            })
        });
        
        if (isCorrect) {
            feedback.innerHTML = '<div class="alert alert-success">Correct! Great job!</div>';
            getNewProblem();
            setTimeout(() => feedback.innerHTML = '', 1000);
        } else {
            wrongAttempts++;
            if (wrongAttempts >= 3) {
                currentProblem.show_answer = true;
                displayProblem(currentProblem);
            }
            feedback.innerHTML = '<div class="alert alert-danger">Not quite. Try again!</div>';
            document.getElementById('answer-input').value = '';
            document.getElementById('answer-input').focus();
        }
    });

    // Allow Enter key to submit answer
    document.getElementById('answer-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            document.getElementById('check-answer').click();
        }
    });

    // Initialize with addition
    document.querySelector('[data-operation="addition"]').click();
});
