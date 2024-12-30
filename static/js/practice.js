let currentOperation = 'addition';
let problemStartTime = null;
let currentProblem = null;
let wrongAttempts = 0;

async function getNewProblem() {
    const level = currentOperation === 'addition' 
        ? document.getElementById('addition-select').value 
        : document.getElementById('multiplication-select').value;
    
    try {
        const response = await fetch('/get_problem', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                operation: currentOperation,
                level: parseInt(level)
            })
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
