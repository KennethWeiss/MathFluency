let currentOperation = 'multiplication';
let problemStartTime = null;
let currentProblem = null;
let wrongAttempts = 0;



// Get CSRF token from meta tag
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

async function getNewProblem() {
    let level;
    
    // If in assignment mode, use assignment level
    if (typeof assignmentId !== 'undefined' && typeof assignmentLevel !== 'undefined') {
        level = assignmentLevel;  // This is already set from practice.html
    } else {
        // Free practice mode - get level from select or use default
        const select = document.querySelector('.level-select:not([style*="display: none"])');
        level = select ? select.value : 1;  // Default to level 1 if select not found
    }
    
    try {
        let requestData = {
            operation: currentOperation,
            level: parseInt(level)
        };

        // Add assignment_id if in assignment mode
        if (typeof assignmentId !== 'undefined') {
            requestData.assignment_id = assignmentId;
            // In assignment mode, use the operation from the server response
            const response = await fetch(`/get_assignment_info/${assignmentId}`, {
                headers: {
                    'X-CSRFToken': getCsrfToken()
                }
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const assignmentData = await response.json();
            requestData.operation = assignmentData.operation;
        }

        const response = await fetch('/get_problem', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
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

        // Check for level up
        if (problemData.level_up) {
            // Show mastery message
            const masteryMessage = `
                <div class="alert alert-success">
                    <h4 class="alert-heading">Level Mastered! 🎉</h4>
                    <p>${problemData.message}</p>
                    <hr>
                    <p class="mb-0">Moving to level ${problemData.new_level}...</p>
                </div>`;
            document.getElementById('feedback').innerHTML = masteryMessage;

            // Update level selector if in free practice mode
            if (typeof assignmentId === 'undefined') {
                const select = document.querySelector('.level-select:not([style*="display: none"])');
                if (select) {
                    select.value = problemData.new_level;
                }
            }

            // Get a new problem after a short delay to show the message
            setTimeout(() => {
                getNewProblem();
            }, 3000);
            return;
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
    // Show answer input and check button
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

// Operation selection
document.addEventListener('DOMContentLoaded', function() {
    // Initialize with addition in free practice mode
    if (typeof assignmentId === 'undefined') {
        // First set up the operation buttons
        document.querySelectorAll('[data-operation]').forEach(button => {
            button.addEventListener('click', function() {
                const operation = this.getAttribute('data-operation');
                currentOperation = operation;
                
                // Update UI
                document.querySelectorAll('[data-operation]').forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');
                
                // Show/hide appropriate level select
                document.querySelectorAll('.level-select').forEach(select => {
                    select.style.display = 'none';
                });
                const operationSelect = document.getElementById(`${operation}-select`);
                if (operationSelect) {
                    operationSelect.style.display = 'block';
                }
                
                getNewProblem();
            });
        });

        // Add event listeners for selection menus
        document.querySelectorAll('.level-select').forEach(select => {
            select.addEventListener('change', getNewProblem);
        });
        
        // Initialize with addition selected
        const additionButton = document.querySelector('[data-operation="addition"]');
        if (additionButton) {
            additionButton.click();  // This will trigger getNewProblem
        }
    } else {
        // In assignment mode, just get the first problem
        getNewProblem();
    }

    // New problem button
    document.getElementById('new-problem').addEventListener('click', getNewProblem);

    // Check answer
    document.getElementById('check-answer').addEventListener('click', async function() {
        const userAnswer = document.getElementById('answer-input').value;
        const correctAnswer = document.getElementById('correct-answer-hidden').value;
        const timeTaken = (Date.now() - problemStartTime) / 1000;  // Convert to seconds
        
        // Check answer on frontend
        const isCorrect = parseInt(userAnswer) === parseInt(correctAnswer);
        const feedback = document.getElementById('feedback');
        
        try {
            // Record attempt
            const requestData = {
                operation: currentOperation,
                level: parseInt(document.querySelector('.level-select:not([style*="display: none"])')?.value || 1),
                problem: document.getElementById('current-problem').textContent,
                answer: parseInt(userAnswer),
                correct_answer: parseInt(correctAnswer),
                is_correct: isCorrect,
                time_taken: timeTaken
            };

            // Only include assignment_id if we're in assignment mode
            if (typeof assignmentId !== 'undefined') {
                requestData.assignment_id = assignmentId;
            }

            const response = await fetch('/check_answer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            
            if (result.is_correct) {
                feedback.innerHTML = '<div class="alert alert-success">Correct! Great job!</div>';
                
                // Update progress bar in assignment mode
                if (typeof assignmentId !== 'undefined' && result.progress) {
                    const progressBar = document.getElementById('assignment-progress');
                    const percentage = (result.progress.problems_correct / result.progress.required_problems * 100).toFixed(0);
                    progressBar.style.width = `${percentage}%`;
                    progressBar.textContent = `${result.progress.problems_correct}/${result.progress.required_problems} correct`;
                }
                
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
        } catch (error) {
            console.error('Error checking answer:', error);
            feedback.innerHTML = `<div class="alert alert-danger">Error checking answer: ${error.message}</div>`;
        }
    });

    // Allow Enter key to submit answer
    document.getElementById('answer-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            document.getElementById('check-answer').click();
        }
    });
});
