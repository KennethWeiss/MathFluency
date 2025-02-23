// Quiz creation form event handlers
document.addEventListener('DOMContentLoaded', function() {
    const operationSelect = document.getElementById('operation');
    if (operationSelect) {  // Only setup if we're on the quiz creation page
        operationSelect.addEventListener('change', function() {
            const operation = this.value;
            const levelSelect = document.getElementById('level');
            
            // Clear existing options
            levelSelect.innerHTML = '';

            let options = [];
            if (operation === 'addition') {
                options = [
                    { value: 1, text: "1: Single Digit - Basic addition of numbers from 0 to 9." },
                    { value: 2, text: "2: Double Digit - Addition of two-digit numbers (10-99)." },
                    { value: 3, text: "3: Make 10 - Problems that require making a total of 10." },
                    { value: 4, text: "4: Add to 100 - Addition problems that sum to 100." },
                    { value: 5, text: "5: Add to 1000 - Addition problems that sum to 1000." }
                ];
            } else if (operation === 'multiplication') {
                options = [
                    { value: 1, text: "1: ×1 Table - Multiplication by 1." },
                    { value: 2, text: "2: ×2 Table - Multiplication by 2." },
                    { value: 3, text: "3: ×3 Table - Multiplication by 3." },
                    { value: 4, text: "4: ×4 Table - Multiplication by 4." },
                    { value: 5, text: "5: ×5 Table - Multiplication by 5." },
                    { value: 6, text: "6: ×6 Table - Multiplication by 6." },
                    { value: 7, text: "7: ×7 Table - Multiplication by 7." },
                    { value: 8, text: "8: ×8 Table - Multiplication by 8." },
                    { value: 9, text: "9: ×9 Table - Multiplication by 9." },
                    { value: 10, text: "10: ×10 Table - Multiplication by 10." },
                    { value: 11, text: "11: ×11 Table - Multiplication by 11." },
                    { value: 12, text: "12: ×12 Table - Multiplication by 12." }
                ];
            }

            // Populate the level select with new options
            options.forEach(option => {
                const newOption = document.createElement('option');
                newOption.value = option.value;
                newOption.textContent = option.text;
                levelSelect.appendChild(newOption);
            });
        });
    }
});

// QuizGame class for managing quiz state and socket communication
class QuizGame {
    constructor(quizId, isTeacher = false) {
        this.quizId = quizId;
        this.isTeacher = isTeacher;
        this.currentQuestionId = null; // Store the current question ID
        this.elements = this.cacheElements();
        
        // Initialize socket connection
        this.socket = io({
            transports: ['websocket'],
            reconnectionAttempts: 5,
            reconnectionDelay: 1000,
            path: '/socket.io'
        });

        this.setupSocketListeners();
        
        // Setup answer input event listener for student view
        const answerInput = document.getElementById('answer');
        if (!this.isTeacher && answerInput) {
            answerInput.addEventListener('keypress', (event) => {
                if (event.key === 'Enter') {
                    event.preventDefault();
                    const answer = parseInt(answerInput.value);
                    if (isNaN(answer)) {
                        alert('Please enter a valid number');
                        return;
                    }
                    this.submitAnswer(answer);
                }
            });
        }
    }

    cacheElements() {
        const elements = {};
        
        // Elements for both views
        elements.status = document.getElementById('quiz-status');
        elements.timer = document.getElementById('timer');
        elements.timerDisplay = document.getElementById('timer-display');
        elements.participantsList = document.getElementById('participants-list');
        elements.leaderboard = document.getElementById('leaderboard');
        
        // Teacher-specific elements
        if (this.isTeacher) {
            elements.startButton = document.getElementById('start-quiz-btn');
            elements.pauseButton = document.getElementById('pause-quiz-btn');
            elements.resumeButton = document.getElementById('resume-quiz-btn');
            elements.endButton = document.getElementById('end-quiz-btn');
            elements.restartButton = document.getElementById('restart-quiz-btn');
        } else {
            // Student-specific elements
            elements.waitingScreen = document.getElementById('waiting-screen');
            elements.quizScreen = document.getElementById('quiz-screen');
            elements.pausedScreen = document.getElementById('paused-screen');
            elements.finishedScreen = document.getElementById('finished-screen');
            elements.problemDisplay = document.getElementById('problem-display');
            elements.answerInput = document.getElementById('answer');
            elements.feedback = document.getElementById('feedback');
            elements.currentScore = document.getElementById('current-score');
            elements.finalScore = document.getElementById('final-score');
        }
        
        return elements;
    }

    setupSocketListeners() {
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.socket.emit('join_quiz', {
                quiz_id: this.quizId,
                is_teacher: this.isTeacher
            });
        });

        this.socket.on('quiz_status_changed', (data) => {
            console.log('Quiz status update:', data);
            if (this.elements.status) {
                this.elements.status.textContent = data.status;
                this.elements.status.className = `badge bg-${data.status === 'active' ? 'success' : data.status === 'paused' ? 'warning' : 'secondary'}`;
            }
            
            if (this.isTeacher) {
                this.updateButtonVisibility(data.status);
            } else {
                this.updateScreenVisibility(data.status);
            }
        });

        this.socket.on('participants_update', (data) => {
            console.log('Participants update:', data);
            this.updateParticipantsList(data.participants);
            this.updateLeaderboard(data.participants);
        });

        this.socket.on('new_problem', (data) => {
            console.log('New problem received:', data);
            if (!this.isTeacher && this.elements.problemDisplay) {
                this.elements.problemDisplay.textContent = data.problem;
                this.currentQuestionId = data.question_id; // Store the question ID
                if (this.elements.answerInput) {
                    this.elements.answerInput.value = '';
                    this.elements.answerInput.focus();
                }
            }
        });

        this.socket.on('score_updated', (data) => {
            console.log('Score update received:', data);
            if (!this.isTeacher && this.elements.currentScore) {
                this.elements.currentScore.textContent = data.score;
            }
        });

        this.socket.on('answer_feedback', (data) => {
            console.log('Answer feedback received:', data);
            if (!this.isTeacher && this.elements.feedback) {
                const feedbackClass = data.correct ? 'text-success' : 'text-danger';
                const feedbackText = data.correct ? 'Correct!' : 'Incorrect';
                this.elements.feedback.textContent = feedbackText;
                this.elements.feedback.className = feedbackClass;
                
                // Clear feedback after a short delay
                setTimeout(() => {
                    this.elements.feedback.textContent = '';
                    this.elements.feedback.className = '';
                }, 2000);
            }
        });

        this.socket.on('error', (error) => {
            console.error('Socket error:', error);
            alert('An error occurred. Please refresh the page and try again.');
        });
    }

    updateButtonVisibility(status) {
        if (!this.isTeacher) return;

        // Clean up status text by removing whitespace and converting to lowercase
        status = status.trim().toLowerCase();
        console.log('Updating button visibility for status:', status);

        // Get all buttons from cached elements
        const buttons = {
            start: document.getElementById('start-quiz-btn'),
            pause: document.getElementById('pause-quiz-btn'),
            resume: document.getElementById('resume-quiz-btn'),
            end: document.getElementById('end-quiz-btn'),
            restart: document.getElementById('restart-quiz-btn')
        };

        // Hide all buttons first
        Object.values(buttons).forEach(button => {
            if (button) {
                button.style.display = 'none';
                button.disabled = false;
            }
        });

        // Show appropriate buttons based on status
        switch (status) {
            case 'waiting':
                if (buttons.start) {
                    console.log('Showing start button');
                    buttons.start.style.display = 'inline-block';
                }
                break;
            case 'active':
                if (buttons.pause) buttons.pause.style.display = 'inline-block';
                if (buttons.end) buttons.end.style.display = 'inline-block';
                break;
            case 'paused':
                if (buttons.resume) buttons.resume.style.display = 'inline-block';
                if (buttons.end) buttons.end.style.display = 'inline-block';
                break;
            case 'finished':
                if (buttons.restart) buttons.restart.style.display = 'inline-block';
                break;
        }
    }

    updateScreenVisibility(status) {
        if (!this.isTeacher) {
            console.log('Updating screen visibility for status:', status);
            
            // Get all screen elements
            const screens = {
                waiting: this.elements.waitingScreen,
                quiz: this.elements.quizScreen,
                paused: this.elements.pausedScreen,
                finished: this.elements.finishedScreen
            };
            
            // Hide all screens first
            Object.values(screens).forEach(screen => {
                if (screen) {
                    screen.classList.add('d-none');
                }
            });
            
            // Show the appropriate screen based on status
            switch (status) {
                case 'waiting':
                    if (screens.waiting) screens.waiting.classList.remove('d-none');
                    break;
                case 'active':
                    if (screens.quiz) screens.quiz.classList.remove('d-none');
                    break;
                case 'paused':
                    if (screens.paused) screens.paused.classList.remove('d-none');
                    break;
                case 'finished':
                    if (screens.finished) screens.finished.classList.remove('d-none');
                    break;
            }
        }
    }

    startQuiz() {
        console.log('Starting quiz...');
        this.socket.emit('start_quiz', { quiz_id: this.quizId });
    }

    pauseQuiz() {
        console.log('Pausing quiz...');
        this.socket.emit('pause_quiz', { quiz_id: this.quizId });
    }

    resumeQuiz() {
        console.log('Resuming quiz...');
        this.socket.emit('resume_quiz', { quiz_id: this.quizId });
    }

    endQuiz() {
        console.log('Ending quiz...');
        this.socket.emit('end_quiz', { quiz_id: this.quizId });
    }

    restartQuiz() {
        console.log('Restarting quiz...');
        this.socket.emit('restart_quiz', { quiz_id: this.quizId });
    }

    copyQuizLink() {
        const linkElement = document.getElementById('quiz-link');
        if (linkElement) {
            const link = linkElement.textContent;
            navigator.clipboard.writeText(link).then(() => {
                alert('Quiz link copied to clipboard!');
            }).catch(err => {
                console.error('Failed to copy link:', err);
                alert('Failed to copy link. Please try selecting and copying manually.');
            });
        }
    }

    submitAnswer(answer) {
        if (this.isTeacher) return;
        
        console.log('Submitting answer:', answer);
        this.socket.emit('submit_answer', {
            quiz_id: this.quizId,
            question_id: this.currentQuestionId, // Include the question ID
            answer: answer
        });
        
        // Clear the answer input
        if (this.elements.answerInput) {
            this.elements.answerInput.value = '';
            this.elements.answerInput.focus();
        }
    }

    updateParticipantsList(participants) {
        if (!this.elements.participantsList) return;
        
        this.elements.participantsList.innerHTML = '';
        if (participants.length === 0) {
            this.elements.participantsList.innerHTML = '<div class="list-group-item">No participants yet</div>';
            return;
        }

        participants.forEach(participant => {
            const item = document.createElement('div');
            item.className = 'list-group-item d-flex justify-content-between align-items-center';
            item.innerHTML = `
                ${participant.username}
                <span class="badge bg-primary rounded-pill">${participant.score}</span>
            `;
            this.elements.participantsList.appendChild(item);
        });
    }

    updateLeaderboard(participants) {
        if (!this.elements.leaderboard) return;
        
        this.elements.leaderboard.innerHTML = '';
        if (participants.length === 0) {
            this.elements.leaderboard.innerHTML = '<div class="list-group-item">No participants yet</div>';
            return;
        }

        // Sort participants by score
        const sortedParticipants = [...participants].sort((a, b) => b.score - a.score);
        
        sortedParticipants.forEach(participant => {
            const item = document.createElement('div');
            item.className = 'list-group-item d-flex justify-content-between align-items-center';
            item.innerHTML = `
                ${participant.username}
                <span class="badge bg-primary rounded-pill">${participant.score}</span>
            `;
            this.elements.leaderboard.appendChild(item);
        });
    }
}
